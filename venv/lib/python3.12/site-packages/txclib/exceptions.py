# -*- coding: utf-8 -*-

"""
Exception classes for the tx client.
"""


class UnInitializedError(Exception):
    """The project directory has not been initialized."""


class UnknownCommandError(Exception):
    """The provided command is not supported."""


class ConfigFileError(Exception):
    """The .tx/config file has missing data"""


class MalformedConfigFile(ConfigFileError):
    pass


class TransifexrcConfigFileError(Exception):
    """The ~/.transifexrc file has missing data"""

# HTTP exceptions


class HttpNotFound(Exception):
    pass


class HttpNotAuthorized(Exception):
    pass


class AuthenticationError(Exception):
    pass
