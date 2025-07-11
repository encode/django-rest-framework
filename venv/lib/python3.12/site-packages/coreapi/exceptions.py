# coding: utf-8
from __future__ import unicode_literals


class CoreAPIException(Exception):
    """
    A base class for all `coreapi` exceptions.
    """
    pass


class ParseError(CoreAPIException):
    """
    Raised when an invalid Core API encoding is encountered.
    """
    pass


class NoCodecAvailable(CoreAPIException):
    """
    Raised when there is no available codec that can handle the given media.
    """
    pass


class NetworkError(CoreAPIException):
    """
    Raised when the transport layer fails to make a request or get a response.
    """
    pass


class LinkLookupError(CoreAPIException):
    """
    Raised when `.action` fails to index a link in the document.
    """
    pass


class ParameterError(CoreAPIException):
    """
    Raised when the parameters passed do not match the link fields.

    * A required field was not included.
    * An unknown field was included.
    * A field was passed an invalid type for the link location/encoding.
    """
    pass


class ErrorMessage(CoreAPIException):
    """
    Raised when the transition returns an error message.
    """
    def __init__(self, error):
        self.error = error

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, repr(self.error))

    def __str__(self):
        return str(self.error)
