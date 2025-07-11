# -*- coding: utf-8 -*-
"""
Contains the crawling logic.
"""
from __future__ import unicode_literals, absolute_import

import base64
import logging
import sys
import time

from pylinkvalidator.bs4 import BeautifulSoup

import pylinkvalidator.compat as compat
from pylinkvalidator.compat import (
    range, HTTPError, get_url_open, unicode,
    get_content_type, get_url_request, get_charset)
from pylinkvalidator.models import (
    Config, WorkerInit, Response, PageCrawl,
    ExceptionStr, Link, SitePage, WorkerInput, TYPE_ATTRIBUTES, HTML_MIME_TYPE,
    MODE_THREAD, MODE_PROCESS, MODE_GREEN, WHEN_ALWAYS, UTF8Class,
    PageStatus, PageSource, PAGE_QUEUED, PAGE_CRAWLED, VERBOSE_QUIET,
    VERBOSE_NORMAL, LazyLogParam)
from pylinkvalidator.reporter import report
from pylinkvalidator.urlutil import (
    get_clean_url_split, get_absolute_url_split,
    is_link, SUPPORTED_SCHEMES)


WORK_DONE = '__WORK_DONE__'


def get_logger(propagate=False):
    """Returns a logger."""
    root_logger = logging.getLogger()

    logger = logging.getLogger(__name__)

    handler = logging.StreamHandler()

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    if root_logger.level != logging.CRITICAL:
        logger.addHandler(handler)
        logger.propagate = propagate
    else:
        logger.addHandler(compat.NullHandler())

    return logger


class SiteCrawler(object):
    """Main crawler/orchestrator"""

    def __init__(self, config, logger):
        self.config = config
        self.start_url_splits = []
        for start_url in config.start_urls:
            self.start_url_splits.append(get_clean_url_split(start_url))
        self.workers = []
        self.input_queue = self.build_queue(config)
        self.output_queue = self.build_queue(config)
        self.logger = logger
        self.site = Site(self.start_url_splits, config, self.logger)

    def build_logger(self):
        return self.logger

    def crawl(self):
        worker_init = WorkerInit(
            self.config.worker_config, self.input_queue,
            self.output_queue, self.build_logger())
        self.workers = self.get_workers(self.config, worker_init)

        queue_size = len(self.start_url_splits)
        for start_url_split in self.start_url_splits:
            self.input_queue.put(WorkerInput(start_url_split, True, 0), False)

        self.start_workers(self.workers, self.input_queue, self.output_queue)

        self.start_progress()

        while True:
            page_crawl = self.output_queue.get()
            queue_size -= 1
            new_worker_inputs = self.process_page_crawl(page_crawl)

            # We only process new pages if we did not exceed configured depth
            for worker_input in new_worker_inputs:
                queue_size += 1
                self.input_queue.put(worker_input, False)

            self.progress(page_crawl, len(self.site.pages), queue_size)

            if queue_size <= 0:
                self.stop_workers(self.workers, self.input_queue,
                                  self.output_queue)
                self.stop_progress()
                return self.site

    def start_progress(self):
        if self.config.options.progress:
            print("Starting crawl...")

    def stop_progress(self):
        if self.config.options.progress:
            print("Crawling Done...\n")

    def progress(self, page_crawl, done_size, queue_size):
        if not self.config.options.progress:
            return

        total = done_size + queue_size
        percent = float(done_size) / float(total) * 100.0

        url = ""
        if page_crawl.final_url_split:
            url = page_crawl.final_url_split.geturl()
        elif page_crawl.original_url_split:
            url = page_crawl.original_url_split.geturl()

        status = page_crawl.status
        if not status:
            status = "error"

        print("{0} - {1} ({2} of {3} - {4:.0f}%)".format(
            status, url, done_size, total, percent))

    def build_queue(self, config):
        """Returns an object implementing the Queue interface."""
        raise NotImplementedError()

    def get_workers(self, config, worker_init):
        """Returns a sequence of workers of the desired type."""
        raise NotImplementedError()

    def start_workers(self, workers, input_queue, output_queue):
        """Start the workers."""
        raise NotImplementedError()

    def stop_workers(self, workers, input_queue, output_queue):
        """Stops the workers."""
        for worker in workers:
            input_queue.put(WORK_DONE)

    def process_page_crawl(self, page_crawl):
        """Returns a sequence of SplitResult to crawl."""
        return self.site.add_crawled_page(page_crawl)


class ThreadSiteCrawler(SiteCrawler):
    """Site Crawler with thread workers."""

    def build_queue(self, config):
        return compat.Queue.Queue()

    def get_workers(self, config, worker_init):
        from threading import Thread
        workers = []
        for _ in range(config.worker_size):
            workers.append(
                Thread(target=crawl_page, kwargs={'worker_init': worker_init}))

        return workers

    def start_workers(self, workers, input_queue, output_queue):
        for worker in workers:
            worker.start()


class ProcessSiteCrawler(SiteCrawler):
    """Site Crawler with process workers."""

    def __init__(self, *args, **kwargs):
        import multiprocessing
        self.manager = multiprocessing.Manager()
        self.ProcessClass = multiprocessing.Process
        super(ProcessSiteCrawler, self).__init__(*args, **kwargs)

    def build_logger(self):
        """We do not want to share a logger."""
        return None

    def build_queue(self, config):
        return self.manager.Queue()

    def get_workers(self, config, worker_init):
        workers = []
        for _ in range(config.worker_size):
            workers.append(self.ProcessClass(
                target=crawl_page, kwargs={'worker_init': worker_init}))

        return workers

    def start_workers(self, workers, input_queue, output_queue):
        for worker in workers:
            worker.start()


class GreenSiteCrawler(SiteCrawler):
    """Site Crawler with green thread workers."""

    def __init__(self, *args, **kwargs):
        from gevent import monkey, queue, Greenlet
        # TODO thread=false should be used to remove useless exception
        # But weird behavior sometimes happen when it is not patched...
        monkey.patch_all()
        self.QueueClass = queue.Queue
        self.GreenClass = Greenlet
        super(GreenSiteCrawler, self).__init__(*args, **kwargs)

    def build_queue(self, config):
        return self.QueueClass()

    def get_workers(self, config, worker_init):
        workers = []
        for _ in range(config.worker_size):
            workers.append(self.GreenClass(
                crawl_page, worker_init=worker_init))

        return workers

    def start_workers(self, workers, input_queue, output_queue):
        for worker in workers:
            worker.start()


class PageCrawler(object):
    """Worker that parses a page and extracts links"""

    def __init__(self, worker_init):
        self.worker_config = worker_init.worker_config
        self.input_queue = worker_init.input_queue
        self.output_queue = worker_init.output_queue
        self.urlopen = get_url_open()
        self.request_class = get_url_request()
        self.logger = worker_init.logger
        if not self.logger:
            # Get a new one!
            self.logger = get_logger()

        # We do this here to allow patching by gevent
        import socket
        self.timeout_exception = socket.timeout

        self.auth_header = None

        if self.worker_config.username and self.worker_config.password:
            base64string = unicode(
                base64.encodestring(
                    '{0}:{1}'.format(
                        self.worker_config.username,
                        self.worker_config.password)
                    .encode("utf-8")), "utf-8")
            self.auth_header = ("Authorization",
                                "Basic {0}".format(base64string))

    def crawl_page_forever(self):
        """Starts page crawling loop for this worker."""

        while True:
            worker_input = self.input_queue.get()

            if worker_input == WORK_DONE:
                # No more work! Pfew!
                return
            else:
                page_crawl = self._crawl_page(worker_input)
                self.output_queue.put(page_crawl)

    def _crawl_page(self, worker_input):
        page_crawl = None
        url_split_to_crawl = worker_input.url_split

        try:
            response = open_url(
                self.urlopen, self.request_class,
                url_split_to_crawl.geturl(), self.worker_config.timeout,
                self.timeout_exception, self.auth_header,
                extra_headers=self.worker_config.extra_headers,
                logger=self.logger)

            if response.exception:
                if response.status:
                    # This is a http error. Good.
                    page_crawl = PageCrawl(
                        original_url_split=url_split_to_crawl,
                        final_url_split=None, status=response.status,
                        is_timeout=False, is_redirect=False, links=[],
                        exception=None, is_html=False,
                        depth=worker_input.depth)
                elif response.is_timeout:
                    # This is a timeout. No need to wrap the exception
                    page_crawl = PageCrawl(
                        original_url_split=url_split_to_crawl,
                        final_url_split=None, status=None,
                        is_timeout=True, is_redirect=False, links=[],
                        exception=None, is_html=False,
                        depth=worker_input.depth)
                else:
                    # Something bad happened when opening the url
                    exception = ExceptionStr(
                        unicode(type(response.exception)),
                        unicode(response.exception))
                    page_crawl = PageCrawl(
                        original_url_split=url_split_to_crawl,
                        final_url_split=None, status=None,
                        is_timeout=False, is_redirect=False, links=[],
                        exception=exception, is_html=False,
                        depth=worker_input.depth)
            else:
                final_url_split = get_clean_url_split(response.final_url)

                message = response.content.info()
                mime_type = get_content_type(message)
                if self.worker_config.prefer_server_encoding:
                    charset = get_charset(message)
                else:
                    charset = None
                links = []

                is_html = mime_type == HTML_MIME_TYPE

                if is_html and worker_input.should_crawl:
                    html_soup = BeautifulSoup(
                        response.content, self.worker_config.parser,
                        from_encoding=charset)
                    links = self.get_links(html_soup, final_url_split)
                else:
                    self.logger.debug(
                        "Won't crawl %s. MIME Type: %s. Should crawl: %s",
                        final_url_split, mime_type,
                        worker_input.should_crawl)

                page_crawl = PageCrawl(
                    original_url_split=url_split_to_crawl,
                    final_url_split=final_url_split, status=response.status,
                    is_timeout=False, is_redirect=response.is_redirect,
                    links=links, exception=None, is_html=is_html,
                    depth=worker_input.depth)
        except Exception as exc:
            exception = ExceptionStr(unicode(type(exc)), unicode(exc))
            page_crawl = PageCrawl(
                original_url_split=url_split_to_crawl,
                final_url_split=None, status=None,
                is_timeout=False, is_redirect=False, links=[],
                exception=exception, is_html=False,
                depth=worker_input.depth)
            self.logger.exception("Exception occurred while crawling a page.")

        return page_crawl

    def get_links(self, html_soup, original_url_split):
        """Get Link for desired types (e.g., a, link, img, script)

        :param html_soup: The page parsed by BeautifulSoup
        :param original_url_split: The URL of the page used to resolve relative
                links.
        :rtype: A sequence of Link objects
        """

        # This is a weird html tag that defines the base URL of a page.
        base_url_split = original_url_split

        bases = html_soup.find_all('base')
        if bases:
            base = bases[0]
            if 'href' in base.attrs:
                base_url_split = get_clean_url_split(base['href'])

        links = []
        for element_type in self.worker_config.types:
            if element_type not in TYPE_ATTRIBUTES:
                raise Exception(
                    "Unknown element type: {0}".format(element_type))
            attribute = TYPE_ATTRIBUTES[element_type]
            element_links = html_soup.find_all(element_type)
            links.extend(self._get_links(
                element_links, attribute, base_url_split, original_url_split))
        return links

    def _get_links(self, elements, attribute, base_url_split,
                   original_url_split):
        links = []
        for element in elements:
            if attribute in element.attrs:
                url = element[attribute]

                if not self.worker_config.strict_mode:
                    url = url.strip()

                if not is_link(url):
                    continue
                abs_url_split = get_absolute_url_split(url, base_url_split)

                if abs_url_split.scheme not in SUPPORTED_SCHEMES:
                    continue

                link = Link(
                    type=unicode(element.name), url_split=abs_url_split,
                    original_url_split=original_url_split,
                    source_str=unicode(element))
                links.append(link)

        return links


class Site(UTF8Class):
    """Contains all the visited and visiting pages of a site.

    This class is NOT thread-safe and should only be accessed by one thread at
    a time!
    """

    def __init__(self, start_url_splits, config, logger=None):
        self.start_url_splits = start_url_splits

        self.pages = {}
        """Map of url:SitePage"""

        self.error_pages = {}
        """Map of url:SitePage with is_ok=False"""

        self.page_statuses = {}
        """Map of url:PageStatus (PAGE_QUEUED, PAGE_CRAWLED)"""

        self.config = config

        self.logger = logger

        for start_url_split in self.start_url_splits:
            self.page_statuses[start_url_split] = PageStatus(PAGE_QUEUED, [])

    @property
    def is_ok(self):
        """Returns True if there is no error page."""
        return len(self.error_pages) == 0

    def add_crawled_page(self, page_crawl):
        """Adds a crawled page. Returns a list of url split to crawl"""
        if page_crawl.original_url_split not in self.page_statuses:
            self.logger.warning("Original URL not seen before!")
            return []

        status = self.page_statuses[page_crawl.original_url_split]

        # Mark it as crawled
        self.page_statuses[page_crawl.original_url_split] = PageStatus(
            PAGE_CRAWLED, None)

        if page_crawl.original_url_split in self.pages:
            self.logger.warning(
                "Original URL already crawled! Concurrency issue!")
            return []

        final_url_split = page_crawl.final_url_split
        if not final_url_split:
            # Happens on 404/500/timeout/error
            final_url_split = page_crawl.original_url_split

        if final_url_split in self.pages:
            # This means that we already processed this final page.
            # It's a redirect. Just add a source
            site_page = self.pages[final_url_split]
            site_page.add_sources(status.sources)
        else:
            # We never crawled this page before
            is_local = self.config.is_local(final_url_split)
            site_page = SitePage(
                final_url_split, page_crawl.status,
                page_crawl.is_timeout, page_crawl.exception,
                page_crawl.is_html, is_local)
            site_page.add_sources(status.sources)
            self.pages[final_url_split] = site_page

            if not site_page.is_ok:
                self.error_pages[final_url_split] = site_page

        return self.process_links(page_crawl)

    def process_links(self, page_crawl):
        links_to_process = []

        source_url_split = page_crawl.original_url_split
        if page_crawl.final_url_split:
            source_url_split = page_crawl.final_url_split

        for link in page_crawl.links:
            url_split = link.url_split
            if not self.config.should_download(url_split):
                self.logger.debug(
                    "Won't download %s. Is local? %s",
                    url_split,
                    LazyLogParam(lambda: self.config.is_local(url_split)))
                continue

            page_status = self.page_statuses.get(url_split, None)
            page_source = PageSource(source_url_split, link.source_str)

            if not page_status:
                # We never encountered this url before
                self.page_statuses[url_split] = PageStatus(
                    PAGE_QUEUED, [page_source])
                should_crawl = self.config.should_crawl(
                    url_split, page_crawl.depth)
                links_to_process.append(WorkerInput(
                    url_split, should_crawl, page_crawl.depth + 1))
            elif page_status.status == PAGE_CRAWLED:
                # Already crawled. Add source
                if url_split in self.pages:
                    self.pages[url_split].add_sources([page_source])
                else:
                    # TODO the final url is different. need a way to link it...
                    pass
            elif page_status.status == PAGE_QUEUED:
                # Already queued for crawling. Add source.
                page_status.sources.append(page_source)

        return links_to_process

    def __unicode__(self):
        return "Site for {0}".format(self.start_url_splits)


def crawl_page(worker_init):
    """Safe redirection to the page crawler"""
    page_crawler = PageCrawler(worker_init)
    page_crawler.crawl_page_forever()


def open_url(open_func, request_class, url, timeout, timeout_exception,
             auth_header=None, extra_headers=None, logger=None):
    """Opens a URL and returns a Response object.

    All parameters are required to be able to use a patched version of the
    Python standard library (i.e., patched by gevent)

    :param open_func: url open function, typicaly urllib2.urlopen
    :param request_class: the request class to use
    :param url: the url to open
    :param timeout: number of seconds to wait before timing out
    :param timeout_exception: the exception thrown by open_func if a timeout
            occurs
    :param auth_header: authentication header
    :param extra_headers: dict of {Header: Value}
    :param logger: logger used to log exceptions
    :rtype: A Response object
    """
    try:
        request = request_class(url)

        if auth_header:
            request.add_header(auth_header[0], auth_header[1])

        if extra_headers:
            for header, value in extra_headers.items():
                request.add_header(header, value)

        output_value = open_func(request, timeout=timeout)
        final_url = output_value.geturl()
        code = output_value.getcode()
        response = Response(
            content=output_value, status=code, exception=None,
            original_url=url, final_url=final_url,
            is_redirect=final_url != url, is_timeout=False)
    except HTTPError as http_error:
        code = http_error.code
        response = Response(
            content=None, status=code, exception=http_error,
            original_url=url, final_url=None, is_redirect=False,
            is_timeout=False)
    except timeout_exception as t_exception:
        response = Response(
            content=None, status=None, exception=t_exception,
            original_url=url, final_url=None, is_redirect=False,
            is_timeout=True)
    except Exception as exc:
        if logger:
            logger.warning("Exception while opening an URL", exc_info=True)
        response = Response(
            content=None, status=None, exception=exc,
            original_url=url, final_url=None, is_redirect=False,
            is_timeout=False)

    return response


def execute_from_command_line():
    """Runs the crawler and retrieves the configuration from the command
       line.
    """
    try:
        start = time.time()
        config = Config()
        config.parse_cli_config()

        logger = configure_logger(config)
        crawler = execute_from_config(config, logger)

        stop = time.time()

        if not crawler.site.is_ok or config.options.when == WHEN_ALWAYS:
            report(crawler.site, config, stop - start, logger)

        if not crawler.site.is_ok:
            sys.exit(1)
    except Exception as e:
        print(e)
        sys.exit(1)


def configure_logger(config):
    """Configures a logger based on the configuration."""
    if config.options.verbose == VERBOSE_QUIET:
        logging.basicConfig(level=logging.CRITICAL)
    elif config.options.verbose == VERBOSE_NORMAL:
        logging.basicConfig(level=logging.WARNING)
    else:
        logging.basicConfig(level=logging.DEBUG)

    logger = get_logger()

    return logger


def execute_from_config(config, logger):
    """Executes a crawler given a config and logger."""
    if not config.start_urls:
        raise Exception("At least one starting URL must be supplied.")

    if config.options.mode == MODE_THREAD:
        crawler = ThreadSiteCrawler(config, logger)
    elif config.options.mode == MODE_PROCESS:
        crawler = ProcessSiteCrawler(config, logger)
    elif config.options.mode == MODE_GREEN:
        crawler = GreenSiteCrawler(config, logger)

    if not crawler:
        raise Exception("Invalid crawling mode supplied.")

    crawler.crawl()

    return crawler
