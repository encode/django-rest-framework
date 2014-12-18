"""
Generic views that provide commonly needed behaviour.
"""
from __future__ import unicode_literals

from django.core.paginator import Paginator, InvalidPage
from django.db.models.query import QuerySet
from django.http import Http404
from django.shortcuts import get_object_or_404 as _get_object_or_404
from django.utils import six
from django.utils.translation import ugettext as _
from rest_framework import views, mixins
from rest_framework.settings import api_settings


def strict_positive_int(integer_string, cutoff=None):
    """
    Cast a string to a strictly positive integer.
    """
    ret = int(integer_string)
    if ret <= 0:
        raise ValueError()
    if cutoff:
        ret = min(ret, cutoff)
    return ret


def get_object_or_404(queryset, *filter_args, **filter_kwargs):
    """
    Same as Django's standard shortcut, but make sure to also raise 404
    if the filter_kwargs don't match the required types.
    """
    try:
        return _get_object_or_404(queryset, *filter_args, **filter_kwargs)
    except (TypeError, ValueError):
        raise Http404


class GenericAPIView(views.APIView):
    """
    Base class for all other generic views.
    """

    # You'll need to either set these attributes,
    # or override `get_queryset()`/`get_serializer_class()`.
    # If you are overriding a view method, it is important that you call
    # `get_queryset()` instead of accessing the `queryset` property directly,
    # as `queryset` will get evaluated only once, and those results are cached
    # for all subsequent requests.
    queryset = None
    serializer_class = None

    # If you want to use object lookups other than pk, set this attribute.
    # For more complex lookup requirements override `get_object()`.
    lookup_field = 'pk'
    lookup_url_kwarg = None

    # Pagination settings
    paginate_by = api_settings.PAGINATE_BY
    paginate_by_param = api_settings.PAGINATE_BY_PARAM
    max_paginate_by = api_settings.MAX_PAGINATE_BY
    pagination_serializer_class = api_settings.DEFAULT_PAGINATION_SERIALIZER_CLASS
    page_kwarg = 'page'

    # The filter backend classes to use for queryset filtering
    filter_backends = api_settings.DEFAULT_FILTER_BACKENDS

    # The following attribute may be subject to change,
    # and should be considered private API.
    paginator_class = Paginator

    def get_serializer_context(self):
        """
        Extra context provided to the serializer class.
        """
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }

    def get_serializer(self, *args, **kwargs):
        """
        Return the serializer instance that should be used for validating and
        deserializing input, and for serializing output.
        """
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)

    def get_pagination_serializer(self, page):
        """
        Return a serializer instance to use with paginated data.
        """
        class SerializerClass(self.pagination_serializer_class):
            class Meta:
                object_serializer_class = self.get_serializer_class()

        pagination_serializer_class = SerializerClass
        context = self.get_serializer_context()
        return pagination_serializer_class(instance=page, context=context)

    def paginate_queryset(self, queryset):
        """
        Paginate a queryset if required, either returning a page object,
        or `None` if pagination is not configured for this view.
        """
        page_size = self.get_paginate_by()
        if not page_size:
            return None

        paginator = self.paginator_class(queryset, page_size)
        page_kwarg = self.kwargs.get(self.page_kwarg)
        page_query_param = self.request.query_params.get(self.page_kwarg)
        page = page_kwarg or page_query_param or 1
        try:
            page_number = paginator.validate_number(page)
        except InvalidPage:
            if page == 'last':
                page_number = paginator.num_pages
            else:
                raise Http404(_("Page is not 'last', nor can it be converted to an int."))
        try:
            page = paginator.page(page_number)
        except InvalidPage as exc:
            error_format = _('Invalid page (%(page_number)s): %(message)s')
            raise Http404(error_format % {
                'page_number': page_number,
                'message': six.text_type(exc)
            })

        return page

    def filter_queryset(self, queryset):
        """
        Given a queryset, filter it with whichever filter backend is in use.

        You are unlikely to want to override this method, although you may need
        to call it either from a list view, or from a custom `get_object`
        method if you want to apply the configured filtering backend to the
        default queryset.
        """
        for backend in self.get_filter_backends():
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset

    def get_filter_backends(self):
        """
        Returns the list of filter backends that this view requires.
        """
        return list(self.filter_backends)

    # The following methods provide default implementations
    # that you may want to override for more complex cases.

    def get_paginate_by(self):
        """
        Return the size of pages to use with pagination.

        If `PAGINATE_BY_PARAM` is set it will attempt to get the page size
        from a named query parameter in the url, eg. ?page_size=100

        Otherwise defaults to using `self.paginate_by`.
        """
        if self.paginate_by_param:
            try:
                return strict_positive_int(
                    self.request.query_params[self.paginate_by_param],
                    cutoff=self.max_paginate_by
                )
            except (KeyError, ValueError):
                pass

        return self.paginate_by

    def get_serializer_class(self):
        """
        Return the class to use for the serializer.
        Defaults to using `self.serializer_class`.

        You may want to override this if you need to provide different
        serializations depending on the incoming request.

        (Eg. admins get full serialization, others get basic serialization)
        """
        assert self.serializer_class is not None, (
            "'%s' should either include a `serializer_class` attribute, "
            "or override the `get_serializer_class()` method."
            % self.__class__.__name__
        )

        return self.serializer_class

    def get_queryset(self):
        """
        Get the list of items for this view.
        This must be an iterable, and may be a queryset.
        Defaults to using `self.queryset`.

        This method should always be used rather than accessing `self.queryset`
        directly, as `self.queryset` gets evaluated only once, and those results
        are cached for all subsequent requests.

        You may want to override this if you need to provide different
        querysets depending on the incoming request.

        (Eg. return a list of items that is specific to the user)
        """
        assert self.queryset is not None, (
            "'%s' should either include a `queryset` attribute, "
            "or override the `get_queryset()` method."
            % self.__class__.__name__
        )

        queryset = self.queryset
        if isinstance(queryset, QuerySet):
            # Ensure queryset is re-evaluated on each request.
            queryset = queryset.all()
        return queryset

    def get_object(self):
        """
        Returns the object the view is displaying.

        You may want to override this if you need to provide non-standard
        queryset lookups.  Eg if objects are referenced using multiple
        keyword arguments in the url conf.
        """
        queryset = self.filter_queryset(self.get_queryset())

        # Perform the lookup filtering.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            (self.__class__.__name__, lookup_url_kwarg)
        )

        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = get_object_or_404(queryset, **filter_kwargs)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj


# Concrete view classes that provide method handlers
# by composing the mixin classes with the base view.

class CreateAPIView(mixins.CreateModelMixin,
                    GenericAPIView):

    """
    Concrete view for creating a model instance.
    """
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class ListAPIView(mixins.ListModelMixin,
                  GenericAPIView):
    """
    Concrete view for listing a queryset.
    """
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class RetrieveAPIView(mixins.RetrieveModelMixin,
                      GenericAPIView):
    """
    Concrete view for retrieving a model instance.
    """
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class DestroyAPIView(mixins.DestroyModelMixin,
                     GenericAPIView):

    """
    Concrete view for deleting a model instance.
    """
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class UpdateAPIView(mixins.UpdateModelMixin,
                    GenericAPIView):

    """
    Concrete view for updating a model instance.
    """
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


class ListCreateAPIView(mixins.ListModelMixin,
                        mixins.CreateModelMixin,
                        GenericAPIView):
    """
    Concrete view for listing a queryset or creating a model instance.
    """
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class RetrieveUpdateAPIView(mixins.RetrieveModelMixin,
                            mixins.UpdateModelMixin,
                            GenericAPIView):
    """
    Concrete view for retrieving, updating a model instance.
    """
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


class RetrieveDestroyAPIView(mixins.RetrieveModelMixin,
                             mixins.DestroyModelMixin,
                             GenericAPIView):
    """
    Concrete view for retrieving or deleting a model instance.
    """
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class RetrieveUpdateDestroyAPIView(mixins.RetrieveModelMixin,
                                   mixins.UpdateModelMixin,
                                   mixins.DestroyModelMixin,
                                   GenericAPIView):
    """
    Concrete view for retrieving, updating or deleting a model instance.
    """
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
