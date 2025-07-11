# -*- coding: utf-8 -*-
"""
Contains the crawling models. We use namedtuple for most models (easier to
pickle, lower footprint, indicates that it is immutable) and we use classes for
objects with mutable states and helper methods.

Classes with crawling logic are declared in the crawler module.
"""
from __future__ import unicode_literals, absolute_import

from collections import namedtuple
from optparse import OptionParser, OptionGroup

from pylinkvalidator.compat import get_safe_str
from pylinkvalidator.urlutil import get_clean_url_split


DEFAULT_TYPES = ['a', 'img', 'script', 'link']


TYPE_ATTRIBUTES = {
    'a': 'href',
    'img': 'src',
    'script': 'src',
    'link': 'href',
}


DEFAULT_TIMEOUT = 10


MODE_THREAD = "thread"
MODE_PROCESS = "process"
MODE_GREEN = "green"


DEFAULT_WORKERS = {
    MODE_THREAD: 1,
    MODE_PROCESS: 1,
    MODE_GREEN: 1000,
}


PARSER_STDLIB = "html.parser"
PARSER_LXML = "lxml"
PARSER_HTML5 = "html5lib"

# TODO Add support for gumbo. Will require some refactoring of the parsing
# logic.
# PARSER_GUMBO = "gumbo"


FORMAT_PLAIN = "plain"
FORMAT_HTML = "html"
FORMAT_JSON = "json"


WHEN_ALWAYS = "always"
WHEN_ON_ERROR = "error"


REPORT_TYPE_ERRORS = "errors"
REPORT_TYPE_SUMMARY = "summary"
REPORT_TYPE_ALL = "all"


VERBOSE_QUIET = "0"
VERBOSE_NORMAL = "1"
VERBOSE_INFO = "2"


HTML_MIME_TYPE = "text/html"


PAGE_QUEUED = '__PAGE_QUEUED__'
PAGE_CRAWLED = '__PAGE_CRAWLED__'

# Note: we use namedtuple to exchange data with workers because they are
# immutable and easy to pickle (as opposed to a class).

WorkerInit = namedtuple("WorkerInit", ["worker_config", "input_queue",
                        "output_queue", "logger"])


WorkerConfig = namedtuple(
    "WorkerConfig",
    ["username", "password", "types", "timeout", "parser", "strict_mode",
     "prefer_server_encoding", "extra_headers"])


WorkerInput = namedtuple("WorkerInput", ["url_split", "should_crawl", "depth"])


Response = namedtuple(
    "Response", ["content", "status", "exception", "original_url",
                 "final_url", "is_redirect", "is_timeout"])


ExceptionStr = namedtuple("ExceptionStr", ["type_name", "message"])


Link = namedtuple("Link", ["type", "url_split", "original_url_split",
                  "source_str"])


PageCrawl = namedtuple(
    "PageCrawl", ["original_url_split", "final_url_split",
                  "status", "is_timeout", "is_redirect", "links",
                  "exception", "is_html", "depth"])


PageStatus = namedtuple("PageStatus", ["status", "sources"])


PageSource = namedtuple("PageSource", ["origin", "origin_str"])


class UTF8Class(object):
    """Handles unicode string from __unicode__() in: __str__() and __repr__()
    """
    def __str__(self):
        return get_safe_str(self.__unicode__())

    def __repr__(self):
        return get_safe_str(self.__unicode__())


class LazyLogParam(object):
    """Lazy Log Parameter that is only evaluated if the logging statement
       is printed"""

    def __init__(self, func):
        self.func = func

    def __str__(self):
        return str(self.func())


class Config(UTF8Class):
    """Contains all the configuration options."""

    def __init__(self):
        # Design note: we only use attributes when options need to be
        # transformed. Otherwise, we use options.
        self.parser = self._build_parser()
        self.options = None
        self.start_urls = []
        self.worker_config = None
        self.accepted_hosts = []
        self.ignored_prefixes = []
        self.worker_size = 0

    def should_crawl(self, url_split, depth):
        """Returns True if url split is local AND depth is acceptable"""
        return (self.options.depth < 0 or depth < self.options.depth) and\
            self.is_local(url_split)

    def is_local(self, url_split):
        """Returns true if url split is in the accepted hosts"""
        return url_split.netloc in self.accepted_hosts

    def should_download(self, url_split):
        """Returns True if the url does not start with an ignored prefix and if
        it is local or outside links are allowed."""
        local = self.is_local(url_split)

        if not self.options.test_outside and not local:
            return False

        url = url_split.geturl()

        for ignored_prefix in self.ignored_prefixes:
            if url.startswith(ignored_prefix):
                return False

        return True

    def parse_cli_config(self):
        """Builds the options and args based on the command line options."""
        (self.options, self.start_urls) = self.parser.parse_args()
        self._parse_config()

    def parse_api_config(self, start_urls, options_dict=None):
        """Builds the options and args based on passed parameters."""
        # TODO Add options
        options = self._get_options(options_dict)
        (self.options, self.start_urls) = self.parser.parse_args(
            options + start_urls)
        self._parse_config()

    def _get_options(self, options_dict):
        if not options_dict:
            options_dict = {}
        options = []
        for key, value in options_dict.items():
            if isinstance(value, bool) and value:
                options.append("--{0}".format(key))
            else:
                options.append("--{0}={1}".format(key, value))
        return options

    def _parse_config(self):
        self.worker_config = self._build_worker_config(self.options)
        self.accepted_hosts = self._build_accepted_hosts(
            self.options, self.start_urls)

        if self.options.ignored_prefixes:
            self.ignored_prefixes = self.options.ignored_prefixes.split(',')

        if self.options.workers:
            self.worker_size = self.options.workers
        else:
            self.worker_size = DEFAULT_WORKERS[self.options.mode]

        if self.options.run_once:
            self.options.depth = 0

    def _build_worker_config(self, options):
        types = options.types.split(',')
        for element_type in types:
            if element_type not in DEFAULT_TYPES:
                raise ValueError("This type is not supported: {0}"
                                 .format(element_type))

        headers = {}
        if options.headers:
            for item in options.headers:
                split = item.split(":")
                if len(split) == 2:
                    headers[split[0]] = split[1]

        return WorkerConfig(
            options.username, options.password, types, options.timeout,
            options.parser, options.strict_mode,
            options.prefer_server_encoding, headers)

    def _build_accepted_hosts(self, options, start_urls):
        hosts = set()
        urls = []

        if self.options.accepted_hosts:
            urls = self.options.accepted_hosts.split(',')
        urls = urls + start_urls

        for url in urls:
            split_result = get_clean_url_split(url)
            hosts.add(split_result.netloc)

        return hosts

    def _build_parser(self):
        # avoid circular references
        import pylinkvalidator
        version = pylinkvalidator.__version__

        parser = OptionParser(
            usage="%prog [options] URL ...",
            version="%prog {0}".format(version))

        parser.add_option(
            "-V", "--verbose", dest="verbose", action="store",
            default=VERBOSE_QUIET, choices=[VERBOSE_QUIET, VERBOSE_NORMAL,
                                            VERBOSE_INFO])

        crawler_group = OptionGroup(
            parser, "Crawler Options",
            "These options modify the way the crawler traverses the site.")
        crawler_group.add_option(
            "-O", "--test-outside", dest="test_outside",
            action="store_true", default=False,
            help="fetch resources from other domains without crawling them")
        crawler_group.add_option(
            "-H", "--accepted-hosts",
            dest="accepted_hosts",  action="store", default=None,
            help="comma-separated list of additional hosts to crawl (e.g., "
            "example.com,subdomain.another.com)")
        crawler_group.add_option(
            "-i", "--ignore", dest="ignored_prefixes",
            action="store", default=None,
            help="comma-separated list of host/path prefixes to ignore "
            "(e.g., www.example.com/ignore_this_and_after/)")
        crawler_group.add_option(
            "-u", "--username", dest="username",
            action="store", default=None,
            help="username to use with basic HTTP authentication")
        crawler_group.add_option(
            "-p", "--password", dest="password",
            action="store", default=None,
            help="password to use with basic HTTP authentication")
        crawler_group.add_option(
            "-D", "--header",
            dest="headers",  action="append", metavar="HEADER",
            help="custom header of the form Header: Value "
            "(repeat for multiple headers)")
        # crawler_group.add_option("-U", "--unique", dest="unique",
        #         action="store_true", default=False)
        crawler_group.add_option(
            "-t", "--types", dest="types", action="store",
            default=",".join(DEFAULT_TYPES),
            help="Comma-separated values of tags to look for when crawling"
            "a site. Default (and supported types): a,img,link,script")
        crawler_group.add_option(
            "-T", "--timeout", dest="timeout",
            type="int", action="store", default=DEFAULT_TIMEOUT,
            help="Seconds to wait before considering that a page timed out")
        crawler_group.add_option(
            "-C", "--strict", dest="strict_mode",
            action="store_true", default=False,
            help="Does not strip href and src attributes from whitespaces")
        crawler_group.add_option(
            "-P", "--progress", dest="progress",
            action="store_true", default=False,
            help="Prints crawler progress in the console")
        crawler_group.add_option(
            "-N", "--run-once", dest="run_once",
            action="store_true", default=False,
            help="Only crawl the first page (eq. to depth=0).")
        crawler_group.add_option(
            "-d", "--depth", dest="depth",
            type="int", action="store", default=-1,
            help="Maximum crawl depth")
        crawler_group.add_option(
            "-e", "--prefer-server-encoding", dest="prefer_server_encoding",
            action="store_true", default=False,
            help="Prefer server encoding if specified. Else detect encoding")
        # TODO Add follow redirect option.

        parser.add_option_group(crawler_group)

        perf_group = OptionGroup(
            parser, "Performance Options",
            "These options can impact the performance of the crawler.")

        perf_group.add_option(
            "-w", "--workers", dest="workers", action="store",
            default=None, type="int",
            help="Number of workers to spawn")
        perf_group.add_option(
            "-m", "--mode", dest="mode", action="store",
            help="Types of workers: thread (default), process, or green",
            default=MODE_THREAD, choices=[MODE_THREAD, MODE_PROCESS,
                                          MODE_GREEN])
        perf_group.add_option(
            "-R", "--parser", dest="parser", action="store",
            help="Types of HTML parse: html.parser (default), lxml, html5lib",
            default=PARSER_STDLIB, choices=[PARSER_STDLIB, PARSER_LXML,
                                            PARSER_HTML5])

        parser.add_option_group(perf_group)

        output_group = OptionGroup(
            parser, "Output Options",
            "These options change the output of the crawler.")

        output_group.add_option(
            "-f", "--format", dest="format", action="store",
            default=FORMAT_PLAIN, choices=[FORMAT_PLAIN],
            help="Format of the report: plain")
        output_group.add_option(
            "-o", "--output", dest="output", action="store",
            default=None,
            help="Path of the file where the report will be printed.")
        output_group.add_option(
            "-W", "--when", dest="when", action="store",
            default=WHEN_ALWAYS, choices=[WHEN_ALWAYS, WHEN_ON_ERROR],
            help="When to print the report. error (only if a "
            "crawling error occurs) or always (default)")
        output_group.add_option(
            "-E", "--report-type", dest="report_type",
            help="Type of report to print: errors (default, summary and "
            "erroneous links), summary, all (summary and all links)",
            action="store", default=REPORT_TYPE_ERRORS,
            choices=[REPORT_TYPE_ERRORS, REPORT_TYPE_SUMMARY, REPORT_TYPE_ALL])
        output_group.add_option(
            "-c", "--console", dest="console",
            action="store_true", default=False,
            help="Prints report to the console in addition to other output"
            " options such as file or email.")
        crawler_group.add_option(
            "-S", "--show-source", dest="show_source",
            action="store_true", default=False,
            help="Show source of links (html) in the report.")

        parser.add_option_group(output_group)

        email_group = OptionGroup(
            parser, "Email Options",
            "These options allows the crawler to send a report by email.")

        email_group.add_option(
            "-a", "--address", dest="address", action="store",
            default=None,
            help="Comma-separated list of email addresses used to send a "
            "report")
        email_group.add_option(
            "--from", dest="from_address", action="store",
            default=None,
            help="Email address to use in the from field of the email "
            "(optional)")
        email_group.add_option(
            "-s", "--smtp", dest="smtp", action="store",
            default=None,
            help="Host of the smtp server")
        email_group.add_option(
            "--port", dest="port", action="store",
            default=25, type="int",
            help="Port of the smtp server (optional)")
        email_group.add_option(
            "--tls", dest="tls", action="store_true",
            default=False,
            help="Use TLS with the email server.")
        email_group.add_option(
            "--subject", dest="subject", action="store",
            default=None,
            help="Subject of the email (optional)")
        email_group.add_option(
            "--smtp-username", dest="smtp_username",
            action="store", default=None,
            help="Username to use with the smtp server (optional)")
        email_group.add_option(
            "--smtp-password", dest="smtp_password",
            action="store", default=None,
            help="Password to use with the smtp server (optional)")

        parser.add_option_group(email_group)

        return parser

    def __unicode__(self):
        return "Configuration - Start URLs: {0} - Options: {1}".format(
            self.start_urls, self.options)


class SitePage(UTF8Class):
    """Contains the crawling result for a page.

    This is a class because we need to keep track of the various sources
    linking to this page and it must be modified as the crawl progresses.
    """

    def __init__(self, url_split, status=200, is_timeout=False, exception=None,
                 is_html=True, is_local=True):
        self.url_split = url_split

        self.original_source = None
        self.sources = []

        self.type = type
        self.status = status
        self.is_timeout = is_timeout
        self.exception = exception
        self.is_html = is_html
        self.is_local = is_local
        self.is_ok = status and status < 400

    def add_sources(self, page_sources):
        self.sources.extend(page_sources)

    def get_status_message(self):
        if self.status:
            if self.status < 400:
                return "ok ({0})".format(self.status)
            elif self.status == 404:
                return "not found (404)"
            else:
                return "error (status={0})".format(self.status)
        elif self.is_timeout:
            return "error (timeout)"
        elif self.exception:
            return "error ({0}): {1}".format(
                self.exception.type_name, self.exception.message)
        else:
            return "error"

    def __unicode__(self):
        return "Resource {0} - {1}".format(
            self.url_split.geturl(), self.status)
