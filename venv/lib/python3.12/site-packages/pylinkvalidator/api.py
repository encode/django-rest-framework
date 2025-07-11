# -*- coding: utf-8 -*-
"""
Contains a simple crawling API to use pylinkvalidator programmatically.

We will do everything to keep functions in this module backward compatible
across versions.
"""
from __future__ import unicode_literals, absolute_import

from pylinkvalidator.crawler import configure_logger, execute_from_config
from pylinkvalidator.models import Config


def crawl(url):
    """Crawls a URL and returns a pylinkvalidator.crawler.Site instance.

    :rtype: A pylinkvalidator.crawler.Site instance
    """
    config = Config()
    config.parse_api_config([url])
    logger = configure_logger(config)
    crawler = execute_from_config(config, logger)

    return crawler.site


def crawl_with_options(urls, options_dict=None, logger_builder=None):
    """Crawls URLs with provided options and logger.

    :param options_dict: Must contain the long name of the command line
            options. (optional)

    :param logger_builder: Function that will be called to instantiate a
            logger. (optional)

    :rtype: A pylinkvalidator.crawler.Site instance
    """

    config = Config()

    config.parse_api_config(urls, options_dict)

    if not logger_builder:
        logger = configure_logger(config)
    else:
        logger = logger_builder()

    # TODO In the future, we will pass the logger builder and not the logger
    # to enable the ProcessSiteCrawler to instantiate its own custom logger.
    crawler = execute_from_config(config, logger)

    return crawler.site
