"""
Pagination serializers determine the structure of the output that should
be used for paginated responses.
"""
from __future__ import unicode_literals
from django.core.paginator import InvalidPage, Paginator as DjangoPaginator
from django.utils import six
from django.utils.translation import ugettext as _
from rest_framework.compat import OrderedDict
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.templatetags.rest_framework import replace_query_param


def _strict_positive_int(integer_string, cutoff=None):
    """
    Cast a string to a strictly positive integer.
    """
    ret = int(integer_string)
    if ret <= 0:
        raise ValueError()
    if cutoff:
        ret = min(ret, cutoff)
    return ret


class BasePagination(object):
    def paginate_queryset(self, queryset, request):
        raise NotImplemented('paginate_queryset() must be implemented.')

    def get_paginated_response(self, data, page, request):
        raise NotImplemented('get_paginated_response() must be implemented.')


class PageNumberPagination(BasePagination):
    """
    A simple page number based style that supports page numbers as
    query parameters. For example:

    http://api.example.org/accounts/?page=4
    http://api.example.org/accounts/?page=4&page_size=100
    """
    # The default page size.
    # Defaults to `None`, meaning pagination is disabled.
    paginate_by = api_settings.PAGINATE_BY

    # Client can control the page using this query parameter.
    page_query_param = 'page'

    # Client can control the page size using this query parameter.
    # Default is 'None'. Set to eg 'page_size' to enable usage.
    paginate_by_param = api_settings.PAGINATE_BY_PARAM

    # Set to an integer to limit the maximum page size the client may request.
    # Only relevant if 'paginate_by_param' has also been set.
    max_paginate_by = api_settings.MAX_PAGINATE_BY

    def paginate_queryset(self, queryset, request, view):
        """
        Paginate a queryset if required, either returning a page object,
        or `None` if pagination is not configured for this view.
        """
        for attr in (
            'paginate_by', 'page_query_param',
            'paginate_by_param', 'max_paginate_by'
        ):
            if hasattr(view, attr):
                setattr(self, attr, getattr(view, attr))

        page_size = self.get_page_size(request)
        if not page_size:
            return None

        paginator = DjangoPaginator(queryset, page_size)
        page_string = request.query_params.get(self.page_query_param, 1)
        try:
            page_number = paginator.validate_number(page_string)
        except InvalidPage:
            if page_string == 'last':
                page_number = paginator.num_pages
            else:
                msg = _(
                    'Choose a valid page number. Page numbers must be a '
                    'whole number, or must be the string "last".'
                )
                raise NotFound(msg)

        try:
            self.page = paginator.page(page_number)
        except InvalidPage as exc:
            msg = _('Invalid page "{page_number}": {message}.').format(
                page_number=page_number, message=six.text_type(exc)
            )
            raise NotFound(msg)

        self.request = request
        return self.page

    def get_paginated_response(self, objects):
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', objects)
        ]))

    def get_page_size(self, request):
        if self.paginate_by_param:
            try:
                return _strict_positive_int(
                    request.query_params[self.paginate_by_param],
                    cutoff=self.max_paginate_by
                )
            except (KeyError, ValueError):
                pass

        return self.paginate_by

    def get_next_link(self):
        if not self.page.has_next():
            return None
        url = self.request.build_absolute_uri()
        page_number = self.page.next_page_number()
        return replace_query_param(url, self.page_query_param, page_number)

    def get_previous_link(self):
        if not self.page.has_previous():
            return None
        url = self.request.build_absolute_uri()
        page_number = self.page.previous_page_number()
        return replace_query_param(url, self.page_query_param, page_number)


class LimitOffsetPagination(BasePagination):
    """
    A limit/offset based style. For example:

    http://api.example.org/accounts/?limit=100
    http://api.example.org/accounts/?offset=400&limit=100
    """
    default_limit = api_settings.PAGINATE_BY
    limit_query_param = 'limit'
    offset_query_param = 'offset'
    max_limit = None

    def paginate_queryset(self, queryset, request, view):
        self.limit = self.get_limit(request)
        self.offset = self.get_offset(request)
        self.count = queryset.count()
        self.request = request
        return queryset[self.offset:self.offset + self.limit]

    def get_paginated_response(self, objects):
        return Response(OrderedDict([
            ('count', self.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', objects)
        ]))

    def get_limit(self, request):
        if self.limit_query_param:
            try:
                return _strict_positive_int(
                    request.query_params[self.limit_query_param],
                    cutoff=self.max_limit
                )
            except (KeyError, ValueError):
                pass

        return self.default_limit

    def get_offset(self, request):
        try:
            return _strict_positive_int(
                request.query_params[self.offset_query_param],
            )
        except (KeyError, ValueError):
            return 0

    def get_next_link(self, page):
        if self.offset + self.limit >= self.count:
            return None
        url = self.request.build_absolute_uri()
        offset = self.offset + self.limit
        return replace_query_param(url, self.offset_query_param, offset)

    def get_previous_link(self, page):
        if self.offset - self.limit < 0:
            return None
        url = self.request.build_absolute_uri()
        offset = self.offset - self.limit
        return replace_query_param(url, self.offset_query_param, offset)
