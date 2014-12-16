# coding: utf-8
from __future__ import unicode_literals
from rest_framework.compat import unicode_http_header
from rest_framework.reverse import _reverse
from rest_framework.templatetags.rest_framework import replace_query_param
from rest_framework.utils.mediatypes import _MediaType
import re


class BaseVersioning(object):
    def determine_version(self, request, *args, **kwargs):
        msg = '{cls}.determine_version() must be implemented.'
        raise NotImplemented(msg.format(
            cls=self.__class__.__name__
        ))

    def reverse(self, viewname, args=None, kwargs=None, request=None, format=None, **extra):
        return _reverse(viewname, args, kwargs, request, format, **extra)


class QueryParameterVersioning(BaseVersioning):
    """
    GET /something/?version=0.1 HTTP/1.1
    Host: example.com
    Accept: application/json
    """
    default_version = None
    version_param = 'version'

    def determine_version(self, request, *args, **kwargs):
        return request.query_params.get(self.version_param)

    def reverse(self, viewname, args=None, kwargs=None, request=None, format=None, **extra):
        url = super(QueryParameterVersioning, self).reverse(
            viewname, args, kwargs, request, format, **extra
        )
        if request.version is not None:
            return replace_query_param(url, self.version_param, request.version)
        return url


class HostNameVersioning(BaseVersioning):
    """
    GET /something/ HTTP/1.1
    Host: v1.example.com
    Accept: application/json
    """
    default_version = None
    hostname_regex = re.compile(r'^([a-zA-Z0-9]+)\.[a-zA-Z0-9]+\.[a-zA-Z0-9]+$')

    def determine_version(self, request, *args, **kwargs):
        hostname, seperator, port = request.get_host().partition(':')
        match = self.hostname_regex.match(hostname)
        if not match:
            return self.default_version
        return match.group(1)

    # We don't need to implement `reverse`, as the hostname will already be
    # preserved as part of the standard `reverse` implementation.


class AcceptHeaderVersioning(BaseVersioning):
    """
    GET /something/ HTTP/1.1
    Host: example.com
    Accept: application/json; version=1.0
    """
    default_version = None
    version_param = 'version'

    def determine_version(self, request, *args, **kwargs):
        media_type = _MediaType(request.accepted_media_type)
        version = media_type.params.get(self.version_param, self.default_version)
        return unicode_http_header(version)

    # We don't need to implement `reverse`, as the versioning is based
    # on the `Accept` header, not on the request URL.


class URLPathVersioning(BaseVersioning):
    """
    To the client this is the same style as `NamespaceVersioning`.
    The difference is in the backend - this implementation uses
    Django's URL keyword arguments to determine the version.

    An example URL conf for two views that accept two different versions.

    urlpatterns = [
        url(r'^(?P<version>{v1,v2})/users/$', users_list, name='users-list'),
        url(r'^(?P<version>{v1,v2})/users/(?P<pk>[0-9]+)/$', users_detail, name='users-detail')
    ]

    GET /1.0/something/ HTTP/1.1
    Host: example.com
    Accept: application/json
    """
    default_version = None
    version_param = 'version'

    def determine_version(self, request, *args, **kwargs):
        return kwargs.get(self.version_param, self.default_version)

    def reverse(self, viewname, args=None, kwargs=None, request=None, format=None, **extra):
        if request.version is not None:
            kwargs = {} if (kwargs is None) else kwargs
            kwargs[self.version_param] = request.version

        return super(URLPathVersioning, self).reverse(
            viewname, args, kwargs, request, format, **extra
        )


class NamespaceVersioning(BaseVersioning):
    """
    To the client this is the same style as `URLPathVersioning`.
    The difference is in the backend - this implementation uses
    Django's URL namespaces to determine the version.

    An example URL conf that is namespaced into two seperate versions

    # users/urls.py
    urlpatterns = [
        url(r'^/users/$', users_list, name='users-list'),
        url(r'^/users/(?P<pk>[0-9]+)/$', users_detail, name='users-detail')
    ]

    # urls.py
    urlpatterns = [
        url(r'^v1/', include('users.urls', namespace='v1')),
        url(r'^v2/', include('users.urls', namespace='v2'))
    ]

    GET /1.0/something/ HTTP/1.1
    Host: example.com
    Accept: application/json
    """
    default_version = None

    def determine_version(self, request, *args, **kwargs):
        resolver_match = getattr(request, 'resolver_match', None)
        if (resolver_match is None or not resolver_match.namespace):
            return self.default_version
        return resolver_match.namespace

    def reverse(self, viewname, args=None, kwargs=None, request=None, format=None, **extra):
        if request.version is not None:
            viewname = request.version + ':' + viewname
        return super(NamespaceVersioning, self).reverse(
            viewname, args, kwargs, request, format, **extra
        )
