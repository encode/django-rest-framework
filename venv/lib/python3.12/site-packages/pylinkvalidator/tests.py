# -*- coding: utf-8 -*-
"""
Unit and integration tests for pylinkvalidator
"""
from __future__ import unicode_literals, absolute_import

import os
import logging
import sys
import time
import threading
import unittest

from pylinkvalidator import api
import pylinkvalidator.compat as compat
from pylinkvalidator.compat import (
    SocketServer, SimpleHTTPServer, get_url_open, get_url_request)
from pylinkvalidator.crawler import (
    open_url, PageCrawler, WORK_DONE, ThreadSiteCrawler, ProcessSiteCrawler,
    get_logger)
from pylinkvalidator.models import (
    Config, WorkerInit, WorkerConfig, WorkerInput, PARSER_STDLIB)
from pylinkvalidator.urlutil import get_clean_url_split, get_absolute_url_split


TEST_FILES_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                              'testfiles')

# Quiet all logging
logging.basicConfig(level=logging.CRITICAL)


# UTILITY CLASSES AND FUNCTIONS ###

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass


def start_http_server():
    """Starts a simple http server for the test files"""
    # For the http handler
    os.chdir(TEST_FILES_DIR)
    handler = SimpleHTTPServer.SimpleHTTPRequestHandler
    handler.extensions_map['.html'] = 'text/html; charset=UTF-8'
    httpd = ThreadedTCPServer(("localhost", 0), handler)
    ip, port = httpd.server_address

    httpd_thread = threading.Thread(target=httpd.serve_forever)
    httpd_thread.setDaemon(True)
    httpd_thread.start()

    return (ip, port, httpd, httpd_thread)


def has_multiprocessing():
    has_multi = False

    try:
        import multiprocessing  # noqa
        has_multi = True
    except Exception:
        pass

    return has_multi


def has_gevent():
    has_gevent = False

    try:
        import gevent  # noqa
        has_gevent = True
    except Exception:
        pass

    return has_gevent


# UNIT AND INTEGRATION TESTS ###


class ConfigTest(unittest.TestCase):

    def setUp(self):
        self.argv = sys.argv

    def tearDown(self):
        sys.argv = self.argv

    def test_accepted_hosts(self):
        sys.argv = ['pylinkvalidator', 'http://www.example.com/']
        config = Config()
        config.parse_cli_config()
        self.assertTrue('www.example.com' in config.accepted_hosts)

        sys.argv = ['pylinkvalidator', '-H', 'www.example.com',
                    'http://example.com', 'foo.com', 'http://www.example.com/',
                    'baz.com']
        config = Config()
        config.parse_cli_config()

        self.assertTrue('www.example.com' in config.accepted_hosts)
        self.assertTrue('example.com' in config.accepted_hosts)
        self.assertTrue('foo.com' in config.accepted_hosts)
        self.assertTrue('baz.com' in config.accepted_hosts)


class URLUtilTest(unittest.TestCase):

    def test_clean_url_split(self):
        self.assertEqual(
            "http://www.example.com",
            get_clean_url_split("www.example.com").geturl())
        self.assertEqual(
            "http://www.example.com",
            get_clean_url_split("//www.example.com").geturl())
        self.assertEqual(
            "http://www.example.com",
            get_clean_url_split("http://www.example.com").geturl())

        self.assertEqual(
            "http://www.example.com/",
            get_clean_url_split("www.example.com/").geturl())
        self.assertEqual(
            "http://www.example.com/",
            get_clean_url_split("//www.example.com/").geturl())
        self.assertEqual(
            "http://www.example.com/",
            get_clean_url_split("http://www.example.com/").geturl())

    def test_get_absolute_url(self):
        base_url_split = get_clean_url_split(
            "https://www.example.com/hello/index.html")
        self.assertEqual(
            "https://www.example2.com/test.js",
            get_absolute_url_split(
                "//www.example2.com/test.js", base_url_split).geturl())
        self.assertEqual(
            "https://www.example.com/hello2/test.html",
            get_absolute_url_split(
                "/hello2/test.html", base_url_split).geturl())
        self.assertEqual(
            "https://www.example.com/hello/test.html",
            get_absolute_url_split("test.html", base_url_split).geturl())
        self.assertEqual(
            "https://www.example.com/test.html",
            get_absolute_url_split("../test.html", base_url_split).geturl())


class CrawlerTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        (cls.ip, cls.port, cls.httpd, cls.httpd_thread) = start_http_server()

        # FIXME replace by thread synchronization on start
        time.sleep(0.2)

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()

    def setUp(self):
        # We must do this because Python 2.6 does not have setUpClass
        # This will only be executed if setUpClass is ignored.
        # It will not be shutdown properly though, but this does not prevent
        # the unit test to run properly
        if not hasattr(self, 'port'):
            (self.ip, self.port, self.httpd, self.httpd_thread) =\
                start_http_server()
            # FIXME replace by thread synchronization on start
            time.sleep(0.2)
        self.argv = sys.argv

        # Need to override root logger level (reset by something)
        logger = logging.getLogger()
        logger.setLevel(logging.CRITICAL)

    def tearDown(self):
        sys.argv = self.argv

    def get_url(self, test_url):
        return "http://{0}:{1}{2}".format(self.ip, self.port, test_url)

    def get_page_crawler(self, url):
        url = self.get_url(url)
        url_split = get_clean_url_split(url)
        input_queue = compat.Queue.Queue()
        output_queue = compat.Queue.Queue()

        worker_config = WorkerConfig(
            username=None, password=None, types=['a', 'img', 'link', 'script'],
            timeout=5, parser=PARSER_STDLIB,
            strict_mode=False, prefer_server_encoding=False,
            extra_headers=[])

        worker_init = WorkerInit(
            worker_config=worker_config,
            input_queue=input_queue, output_queue=output_queue,
            logger=get_logger())

        page_crawler = PageCrawler(worker_init)

        return page_crawler, url_split

    def test_404(self):
        urlopen = get_url_open()
        import socket
        url = self.get_url("/does_not_exist.html")
        response = open_url(
            urlopen, get_url_request(), url, 5, socket.timeout)

        self.assertEqual(404, response.status)
        self.assertTrue(response.exception is not None)

    def test_200(self):
        urlopen = get_url_open()
        import socket
        url = self.get_url("/index.html")
        response = open_url(urlopen, get_url_request(), url, 5, socket.timeout)

        self.assertEqual(200, response.status)
        self.assertTrue(response.exception is None)

    def test_301(self):
        urlopen = get_url_open()
        import socket
        url = self.get_url("/sub")
        response = open_url(urlopen, get_url_request(), url, 5, socket.timeout)

        self.assertEqual(200, response.status)
        self.assertTrue(response.is_redirect)

    def test_crawl_page(self):
        page_crawler, url_split = self.get_page_crawler("/index.html")
        page_crawl = page_crawler._crawl_page(WorkerInput(url_split, True, 0))

        self.assertEqual(200, page_crawl.status)
        self.assertTrue(page_crawl.is_html)
        self.assertFalse(page_crawl.is_timeout)
        self.assertFalse(page_crawl.is_redirect)
        self.assertTrue(page_crawl.exception is None)

        a_links = [link for link in page_crawl.links if link.type == 'a']
        img_links = [link for link in page_crawl.links if link.type == 'img']
        script_links = [link for link in page_crawl.links
                        if link.type == 'script']
        link_links = [link for link in page_crawl.links if link.type == 'link']

        self.assertEqual(5, len(a_links))
        self.assertEqual(1, len(img_links))
        self.assertEqual(1, len(script_links))
        self.assertEqual(1, len(link_links))

    def test_crawl_resource(self):
        page_crawler, url_split = self.get_page_crawler("/sub/small_image.gif")
        page_crawl = page_crawler._crawl_page(WorkerInput(url_split, True, 0))

        self.assertEqual(200, page_crawl.status)
        self.assertFalse(page_crawl.links)
        self.assertFalse(page_crawl.is_html)
        self.assertFalse(page_crawl.is_timeout)
        self.assertFalse(page_crawl.is_redirect)
        self.assertTrue(page_crawl.exception is None)

    def test_base_url(self):
        page_crawler, url_split = self.get_page_crawler("/alone.html")
        page_crawl = page_crawler._crawl_page(WorkerInput(url_split, True, 0))

        self.assertEqual(1, len(page_crawl.links))
        self.assertEqual(
            'http://www.example.com/test.html',
            page_crawl.links[0].url_split.geturl())

    def test_crawl_404(self):
        page_crawler, url_split = self.get_page_crawler(
            "/sub/small_image_bad.gif")
        page_crawl = page_crawler._crawl_page(WorkerInput(url_split, True, 0))

        self.assertEqual(404, page_crawl.status)
        self.assertFalse(page_crawl.links)
        self.assertFalse(page_crawl.is_html)
        self.assertFalse(page_crawl.is_timeout)
        self.assertFalse(page_crawl.is_redirect)

    def test_page_crawler(self):
        page_crawler, url_split = self.get_page_crawler("/index.html")
        input_queue = page_crawler.input_queue
        output_queue = page_crawler.output_queue

        input_queue.put(WorkerInput(url_split, True, 0))
        input_queue.put(WORK_DONE)
        page_crawler.crawl_page_forever()

        page_crawl = output_queue.get()

        self.assertEqual(200, page_crawl.status)
        self.assertTrue(len(page_crawl.links) > 0)

    def _run_crawler_plain(
            self, crawler_class, other_options=None, url="/index.html"):
        url = self.get_url(url)
        sys.argv = ['pylinkvalidator', "-m", "process", url]
        if not other_options:
            other_options = []
        sys.argv.extend(other_options)
        config = Config()
        config.parse_cli_config()

        crawler = crawler_class(config, get_logger())
        crawler.crawl()

        return crawler.site

    def test_site_thread_crawler_plain(self):
        site = self._run_crawler_plain(ThreadSiteCrawler)
        self.assertEqual(11, len(site.pages))
        self.assertEqual(1, len(site.error_pages))

    def test_site_process_crawler_plain(self):
        if not has_multiprocessing():
            return
        site = self._run_crawler_plain(ProcessSiteCrawler)
        self.assertEqual(11, len(site.pages))
        self.assertEqual(1, len(site.error_pages))

    def test_run_once(self):
        site = self._run_crawler_plain(ThreadSiteCrawler, ["--run-once"])

        # 8 pages linked on the index
        self.assertEqual(8, len(site.pages))
        self.assertEqual(0, len(site.error_pages))

    def test_depth_0(self):
        site = self._run_crawler_plain(
            ThreadSiteCrawler, ["--depth", "0"], "/depth/root.html")
        # 3 pages linked on the root (root, 0, 0b)
        self.assertEqual(3, len(site.pages))
        self.assertEqual(0, len(site.error_pages))

        site = self._run_crawler_plain(
            ThreadSiteCrawler, ["--run-once"], "/depth/root.html")
        # Same as depth = 0
        self.assertEqual(3, len(site.pages))
        self.assertEqual(0, len(site.error_pages))

        site = self._run_crawler_plain(
            ThreadSiteCrawler, ["--depth", "1"], "/depth/root.html")
        # 4 pages linked on the root (root, 0, 0b, 1)
        self.assertEqual(4, len(site.pages))
        self.assertEqual(0, len(site.error_pages))

        site = self._run_crawler_plain(
            ThreadSiteCrawler, ["--depth", "10"], "/depth/root.html")
        # 3 pages linked on the root (root, 0, 0b)
        self.assertEqual(7, len(site.pages))
        self.assertEqual(1, len(site.error_pages))

    def test_strict_mode(self):
        site = self._run_crawler_plain(ThreadSiteCrawler, ["--strict"])

        # The placeholdit is interpreted as a relative url
        # So 12 "good" urls and 1 bad.
        self.assertEqual(12, len(site.pages))

        # Python 3 returns an error. There was a change in urllib.
        # In general, strict mode should be false, which is the default
        # This avoids these silly differences
        self.assertTrue(len(site.error_pages) >= 1)

    def test_site_gevent_crawler_plain(self):
        if not has_gevent():
            return
        # TODO test gevent. Cannot use threaded simple http server :-(
        self.assertTrue(True)

    def test_api(self):
        url = self.get_url("/index.html")

        site = api.crawl(url)
        self.assertEqual(11, len(site.pages))
        self.assertEqual(1, len(site.error_pages))

    def test_api_with_options(self):
        url = self.get_url("/index.html")

        site = api.crawl_with_options([url], {"run-once": True, "workers": 2})
        self.assertEqual(8, len(site.pages))
        self.assertEqual(0, len(site.error_pages))

    def test_api_with_options_2(self):
        site = self._run_crawler_plain(
            ThreadSiteCrawler,
            ["--prefer-server-encoding", "--header", "\"XKey: XValue\"",
             "--header", "\"XKey2: XValue2\"", "--run-once"], "/index.html")
        self.assertEqual(8, len(site.pages))
        self.assertEqual(0, len(site.error_pages))

    def test_unicode(self):
        site = self._run_crawler_plain(
            ThreadSiteCrawler, ["--prefer-server-encoding"], "/é.html")
        # 3 pages linked on the root (root, 0, 0b)
        self.assertEqual(2, len(site.pages))
        self.assertEqual(0, len(site.error_pages))
