# coding: utf-8
from __future__ import unicode_literals
from collections import OrderedDict
from coreapi import exceptions, utils
from coreapi.compat import cookiejar, urlparse
from coreapi.document import Document, Object, Link, Array, Error
from coreapi.transports.base import BaseTransport
from coreapi.utils import guess_filename, is_file, File
import collections
import requests
import itypes
import mimetypes
import uritemplate
import warnings


Params = collections.namedtuple('Params', ['path', 'query', 'data', 'files'])
empty_params = Params({}, {}, {}, {})


class ForceMultiPartDict(dict):
    """
    A dictionary that always evaluates as True.
    Allows us to force requests to use multipart encoding, even when no
    file parameters are passed.
    """
    def __bool__(self):
        return True

    def __nonzero__(self):
        return True


class BlockAll(cookiejar.CookiePolicy):
    """
    A cookie policy that rejects all cookies.
    Used to override the default `requests` behavior.
    """
    return_ok = set_ok = domain_return_ok = path_return_ok = lambda self, *args, **kwargs: False
    netscape = True
    rfc2965 = hide_cookie2 = False


class DomainCredentials(requests.auth.AuthBase):
    """
    Custom auth class to support deprecated 'credentials' argument.
    """
    allow_cookies = False
    credentials = None

    def __init__(self, credentials=None):
        self.credentials = credentials

    def __call__(self, request):
        if not self.credentials:
            return request

        # Include any authorization credentials relevant to this domain.
        url_components = urlparse.urlparse(request.url)
        host = url_components.hostname
        if host in self.credentials:
            request.headers['Authorization'] = self.credentials[host]
        return request


class CallbackAdapter(requests.adapters.HTTPAdapter):
    """
    Custom requests HTTP adapter, to support deprecated callback arguments.
    """
    def __init__(self, request_callback=None, response_callback=None):
        self.request_callback = request_callback
        self.response_callback = response_callback

    def send(self, request, **kwargs):
        if self.request_callback is not None:
            self.request_callback(request)
        response = super(CallbackAdapter, self).send(request, **kwargs)
        if self.response_callback is not None:
            self.response_callback(response)
        return response


def _get_method(action):
    if not action:
        return 'GET'
    return action.upper()


def _get_encoding(encoding):
    if not encoding:
        return 'application/json'
    return encoding


def _get_params(method, encoding, fields, params=None):
    """
    Separate the params into the various types.
    """
    if params is None:
        return empty_params

    field_map = {field.name: field for field in fields}

    path = {}
    query = {}
    data = {}
    files = {}

    errors = {}

    # Ensure graceful behavior in edge-case where both location='body' and
    # location='form' fields are present.
    seen_body = False

    for key, value in params.items():
        if key not in field_map or not field_map[key].location:
            # Default is 'query' for 'GET' and 'DELETE', and 'form' for others.
            location = 'query' if method in ('GET', 'DELETE') else 'form'
        else:
            location = field_map[key].location

        if location == 'form' and encoding == 'application/octet-stream':
            # Raw uploads should always use 'body', not 'form'.
            location = 'body'

        try:
            if location == 'path':
                path[key] = utils.validate_path_param(value)
            elif location == 'query':
                query[key] = utils.validate_query_param(value)
            elif location == 'body':
                data = utils.validate_body_param(value, encoding=encoding)
                seen_body = True
            elif location == 'form':
                if not seen_body:
                    data[key] = utils.validate_form_param(value, encoding=encoding)
        except exceptions.ParameterError as exc:
            errors[key] = "%s" % exc

    if errors:
        raise exceptions.ParameterError(errors)

    # Move any files from 'data' into 'files'.
    if isinstance(data, dict):
        for key, value in list(data.items()):
            if is_file(data[key]):
                files[key] = data.pop(key)

    return Params(path, query, data, files)


def _get_url(url, path_params):
    """
    Given a templated URL and some parameters that have been provided,
    expand the URL.
    """
    if path_params:
        return uritemplate.expand(url, path_params)
    return url


def _get_headers(url, decoders):
    """
    Return a dictionary of HTTP headers to use in the outgoing request.
    """
    accept_media_types = decoders[0].get_media_types()
    if '*/*' not in accept_media_types:
        accept_media_types.append('*/*')

    headers = {
        'accept': ', '.join(accept_media_types),
        'user-agent': 'coreapi'
    }

    return headers


def _get_upload_headers(file_obj):
    """
    When a raw file upload is made, determine the Content-Type and
    Content-Disposition headers to use with the request.
    """
    name = guess_filename(file_obj)
    content_type = None
    content_disposition = None

    # Determine the content type of the upload.
    if getattr(file_obj, 'content_type', None):
        content_type = file_obj.content_type
    elif name:
        content_type, encoding = mimetypes.guess_type(name)

    # Determine the content disposition of the upload.
    if name:
        content_disposition = 'attachment; filename="%s"' % name

    return {
        'Content-Type': content_type or 'application/octet-stream',
        'Content-Disposition': content_disposition or 'attachment'
    }


def _build_http_request(session, url, method, headers=None, encoding=None, params=empty_params):
    """
    Make an HTTP request and return an HTTP response.
    """
    opts = {
        "headers": headers or {}
    }

    if params.query:
        opts['params'] = params.query

    if params.data or params.files:
        if encoding == 'application/json':
            opts['json'] = params.data
        elif encoding == 'multipart/form-data':
            opts['data'] = params.data
            opts['files'] = ForceMultiPartDict(params.files)
        elif encoding == 'application/x-www-form-urlencoded':
            opts['data'] = params.data
        elif encoding == 'application/octet-stream':
            if isinstance(params.data, File):
                opts['data'] = params.data.content
            else:
                opts['data'] = params.data
            upload_headers = _get_upload_headers(params.data)
            opts['headers'].update(upload_headers)

    request = requests.Request(method, url, **opts)
    return session.prepare_request(request)


def _coerce_to_error_content(node):
    """
    Errors should not contain nested documents or links.
    If we get a 4xx or 5xx response with a Document, then coerce
    the document content into plain data.
    """
    if isinstance(node, (Document, Object)):
        # Strip Links from Documents, treat Documents as plain dicts.
        return OrderedDict([
            (key, _coerce_to_error_content(value))
            for key, value in node.data.items()
        ])
    elif isinstance(node, Array):
        # Strip Links from Arrays.
        return [
            _coerce_to_error_content(item)
            for item in node
            if not isinstance(item, Link)
        ]
    return node


def _coerce_to_error(obj, default_title):
    """
    Given an arbitrary return result, coerce it into an Error instance.
    """
    if isinstance(obj, Document):
        return Error(
            title=obj.title or default_title,
            content=_coerce_to_error_content(obj)
        )
    elif isinstance(obj, dict):
        return Error(title=default_title, content=obj)
    elif isinstance(obj, list):
        return Error(title=default_title, content={'messages': obj})
    elif obj is None:
        return Error(title=default_title)
    return Error(title=default_title, content={'message': obj})


def _decode_result(response, decoders, force_codec=False):
    """
    Given an HTTP response, return the decoded Core API document.
    """
    if response.content:
        # Content returned in response. We should decode it.
        if force_codec:
            codec = decoders[0]
        else:
            content_type = response.headers.get('content-type')
            codec = utils.negotiate_decoder(decoders, content_type)

        options = {
            'base_url': response.url
        }
        if 'content-type' in response.headers:
            options['content_type'] = response.headers['content-type']
        if 'content-disposition' in response.headers:
            options['content_disposition'] = response.headers['content-disposition']

        result = codec.load(response.content, **options)
    else:
        # No content returned in response.
        result = None

    # Coerce 4xx and 5xx codes into errors.
    is_error = response.status_code >= 400 and response.status_code <= 599
    if is_error and not isinstance(result, Error):
        default_title = '%d %s' % (response.status_code, response.reason)
        result = _coerce_to_error(result, default_title=default_title)

    return result


def _handle_inplace_replacements(document, link, link_ancestors):
    """
    Given a new document, and the link/ancestors it was created,
    determine if we should:

    * Make an inline replacement and then return the modified document tree.
    * Return the new document as-is.
    """
    if not link.transform:
        if link.action.lower() in ('put', 'patch', 'delete'):
            transform = 'inplace'
        else:
            transform = 'new'
    else:
        transform = link.transform

    if transform == 'inplace':
        root = link_ancestors[0].document
        keys_to_link_parent = link_ancestors[-1].keys
        if document is None:
            return root.delete_in(keys_to_link_parent)
        return root.set_in(keys_to_link_parent, document)

    return document


class HTTPTransport(BaseTransport):
    schemes = ['http', 'https']

    def __init__(self, credentials=None, headers=None, auth=None, session=None, request_callback=None, response_callback=None):
        if headers:
            headers = {key.lower(): value for key, value in headers.items()}
        if session is None:
            session = requests.Session()
        if auth is not None:
            session.auth = auth
        if not getattr(session.auth, 'allow_cookies', False):
            session.cookies.set_policy(BlockAll())

        if credentials is not None:
            warnings.warn(
                "The 'credentials' argument is now deprecated in favor of 'auth'.",
                DeprecationWarning
            )
            auth = DomainCredentials(credentials)
        if request_callback is not None or response_callback is not None:
            warnings.warn(
                "The 'request_callback' and 'response_callback' arguments are now deprecated. "
                "Use a custom 'session' instance instead.",
                DeprecationWarning
            )
            session.mount('https://', CallbackAdapter(request_callback, response_callback))
            session.mount('http://', CallbackAdapter(request_callback, response_callback))

        self._headers = itypes.Dict(headers or {})
        self._session = session

    @property
    def headers(self):
        return self._headers

    def transition(self, link, decoders, params=None, link_ancestors=None, force_codec=False):
        session = self._session
        method = _get_method(link.action)
        encoding = _get_encoding(link.encoding)
        params = _get_params(method, encoding, link.fields, params)
        url = _get_url(link.url, params.path)
        headers = _get_headers(url, decoders)
        headers.update(self.headers)

        request = _build_http_request(session, url, method, headers, encoding, params)
        response = session.send(request)
        result = _decode_result(response, decoders, force_codec)

        if isinstance(result, Document) and link_ancestors:
            result = _handle_inplace_replacements(result, link, link_ancestors)

        if isinstance(result, Error):
            raise exceptions.ErrorMessage(result)

        return result
