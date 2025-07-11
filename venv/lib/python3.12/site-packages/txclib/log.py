# -*- coding: utf-8 -*-

"""
Add logging capabilities to tx-client.
"""

import sys
import logging

_logger = logging.getLogger('urllib3')
_logger.setLevel(logging.CRITICAL)

_logger = logging.getLogger('txclib')
_logger.setLevel(logging.INFO)

_formatter = logging.Formatter('tx %(levelname)s: %(message)s')

_error_handler = logging.StreamHandler(sys.stderr)
_error_handler.setLevel(logging.ERROR)
_error_handler.setFormatter(_formatter)
_logger.addHandler(_error_handler)

_msg_handler = logging.StreamHandler(sys.stdout)
_msg_handler.setLevel(logging.DEBUG)
_msg_handler.setFormatter(_formatter)
_msg_filter = logging.Filter()
_msg_filter.filter = lambda r: r.levelno < logging.ERROR
_msg_handler.addFilter(_msg_filter)
_logger.addHandler(_msg_handler)

logger = _logger


def set_log_level(level):
    """Set the level for the logger.

    Args:
        level: A string among DEBUG, INFO, WARNING, ERROR, CRITICAL.
    """
    logger.setLevel(getattr(logging, level))
