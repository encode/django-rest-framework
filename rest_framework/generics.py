"""
Generic views that provide commonly needed behaviour.
"""
from __future__ import unicode_literals

from django.core.exceptions import ImproperlyConfigured
from django.core.paginator import Paginator, InvalidPage
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from rest_framework import views, mixins
from rest_framework.exceptions import ConfigurationError
from rest_framework.settings import api_settings
import warnings


class GenericAPIView(views.APIView):
    """
    Base class for all other generic views.
    """

    # You'll need to either set these attributes,
    # or override `get_queryset()`/`get_serializer_class()`.
    queryset = None
    serializer_class = None

    # This shortcut may be used instead of setting either or both
    # of the `queryset`/`serializer_class` attributes, although using
    # the explicit style is generally preferred.
    model = None

    # If you want to use object lookups other than pk, set this attribute.
    # For more complex lookup requirements override `get_object()`.
    lookup_field = 'pk'

    # Pagination settings
    paginate_by = api_settings.PAGINATE_BY
    paginate_by_param = api_settings.PAGINATE_BY_PARAM
    pagination_serializer_class = api_settings.DEFAULT_PAGINATION_SERIALIZER_CLASS
    page_kwarg = 'page'

    # The filter backend classes to use for queryset filtering
    filter_backends = api_settings.DEFAULT_FILTER_BACKENDS

    # The following attributes may be subject to change,
    # and should be considered private API.
    model_serializer_class = api_settings.DEFAULT_MODEL_SERIALIZER_CLASS
    paginator_class = Paginator

    ######################################
    # These are pending deprecation...

    pk_url_kwarg = 'pk'
    slug_url_kwarg = 'slug'
    slug_field = 'slug'
    allow_empty = True
    filter_backend = api_settings.FILTER_BACKEND

    def get_serializer_context(self):
        """
        Extra context provided to the serializer class.
        """
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }

    def get_serializer(self, instance=None, data=None,
                       files=None, many=False, partial=False):
        """
        Return the serializer instance that should be used for validating and
        deserializing input, and for serializing output.
        """
        serializer_class = self.get_serializer_class()
        context = self.get_serializer_context()
        return serializer_class(instance, data=data, files=files,
                                many=many, partial=partial, context=context)

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

    def paginate_queryset(self, queryset, page_size=None):
        """
        Paginate a queryset if required, either returning a page object,
        or `None` if pagination is not configured for this view.
        """
        deprecated_style = False
        if page_size is not None:
            warnings.warn('The `page_size` parameter to `paginate_queryset()` '
                          'is due to be deprecated. '
                          'Note that the return style of this method is also '
                          'changed, and will simply return a page object '
                          'when called without a `page_size` argument.',
                          PendingDeprecationWarning, stacklevel=2)
            deprecated_style = True
        else:
            # Determine the required page size.
            # If pagination is not configured, simply return None.
            page_size = self.get_paginate_by()
            if not page_size:
                return None

        if not self.allow_empty:
            warnings.warn(
                'The `allow_empty` parameter is due to be deprecated. '
                'To use `allow_empty=False` style behavior, You should override '
                '`get_queryset()` and explicitly raise a 404 on empty querysets.',
                PendingDeprecationWarning, stacklevel=2
            )

        paginator = self.paginator_class(queryset, page_size,
                                         allow_empty_first_page=self.allow_empty)
        page_kwarg = self.kwargs.get(self.page_kwarg)
        page_query_param = self.request.QUERY_PARAMS.get(self.page_kwarg)
        page = page_kwarg or page_query_param or 1
        try:
            page_number = int(page)
        except ValueError:
            if page == 'last':
                page_number = paginator.num_pages
            else:
                raise Http404(_("Page is not 'last', nor can it be converted to an int."))
        try:
            page = paginator.page(page_number)
        except InvalidPage as e:
            raise Http404(_('Invalid page (%(page_number)s): %(message)s') % {
                                'page_number': page_number,
                                'message': str(e)
            })

        if deprecated_style:
            return (paginator, page, page.object_list, page.has_other_pages())
        return page

    def filter_queryset(self, queryset):
        """
        Given a queryset, filter it with whichever filter backend is in use.

        You are unlikely to want to override this method, although you may need
        to call it either from a list view, or from a custom `get_object`
        method if you want to apply the configured filtering backend to the
        default queryset.
        """
        filter_backends = self.filter_backends or []
        if not filter_backends and self.filter_backend:
            warnings.warn(
                'The `filter_backend` attribute and `FILTER_BACKEND` setting '
                'are due to be deprecated in favor of a `filter_backends` '
                'attribute and `DEFAULT_FILTER_BACKENDS` setting, that take '
                'a *list* of filter backend classes.',
                PendingDeprecationWarning, stacklevel=2
            )
            filter_backends = [self.filter_backend]

        for backend in filter_backends:
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset

    ########################
    ### The following methods provide default implementations
    ### that you may want to override for more complex cases.

    def get_paginate_by(self, queryset=None):
        """
        Return the size of pages to use with pagination.

        If `PAGINATE_BY_PARAM` is set it will attempt to get the page size
        from a named query parameter in the url, eg. ?page_size=100

        Otherwise defaults to using `self.paginate_by`.
        """
        if queryset is not None:
            warnings.warn('The `queryset` parameter to `get_paginate_by()` '
                          'is due to be deprecated.',
                          PendingDeprecationWarning, stacklevel=2)

        if self.paginate_by_param:
            query_params = self.request.QUERY_PARAMS
            try:
                return int(query_params[self.paginate_by_param])
            except (KeyError, ValueError):
                pass

        return self.paginate_by

    def get_serializer_class(self):
        """
        Return the class to use for the serializer.
        Defaults to using `self.serializer_class`.

        You may want to override this if you need to provide different
        serializations depending on the incoming request.

        (Eg. admins get full serialization, others get basic serilization)
        """
        serializer_class = self.serializer_class
        if serializer_class is not None:
            return serializer_class

        assert self.model is not None, \
            "'%s' should either include a 'serializer_class' attribute, " \
            "or use the 'model' attribute as a shortcut for " \
            "automatically generating a serializer class." \
            % self.__class__.__name__

        class DefaultSerializer(self.model_serializer_class):
            class Meta:
                model = self.model
        return DefaultSerializer

    def get_queryset(self):
        """
        Get the list of items for this view.
        This must be an iterable, and may be a queryset.
        Defaults to using `self.queryset`.

        You may want to override this if you need to provide different
        querysets depending on the incoming request.

        (Eg. return a list of items that is specific to the user)
        """
        if self.queryset is not None:
            return self.queryset._clone()

        if self.model is not None:
            return self.model._default_manager.all()

        raise ImproperlyConfigured("'%s' must define 'queryset' or 'model'"
                                    % self.__class__.__name__)

    def get_object(self, queryset=None):
        """
        Returns the object the view is displaying.

        You may want to override this if you need to provide non-standard
        queryset lookups.  Eg if objects are referenced using multiple
        keyword arguments in the url conf.
        """
        # Determine the base queryset to use.
        if queryset is None:
            queryset = self.filter_queryset(self.get_queryset())
        else:
            pass  # Deprecation warning

        # Perform the lookup filtering.
        pk = self.kwargs.get(self.pk_url_kwarg, None)
        slug = self.kwargs.get(self.slug_url_kwarg, None)
        lookup = self.kwargs.get(self.lookup_field, None)

        if lookup is not None:
            filter_kwargs = {self.lookup_field: lookup}
        elif pk is not None and self.lookup_field == 'pk':
            warnings.warn(
                'The `pk_url_kwarg` attribute is due to be deprecated. '
                'Use the `lookup_field` attribute instead',
                PendingDeprecationWarning
            )
            filter_kwargs = {'pk': pk}
        elif slug is not None and self.lookup_field == 'pk':
            warnings.warn(
                'The `slug_url_kwarg` attribute is due to be deprecated. '
                'Use the `lookup_field` attribute instead',
                PendingDeprecationWarning
            )
            filter_kwargs = {self.slug_field: slug}
        else:
            raise ConfigurationError(
                'Expected view %s to be called with a URL keyword argument '
                'named "%s". Fix your URL conf, or set the `.lookup_field` '
                'attribute on the view correctly.' %
                (self.__class__.__name__, self.lookup_field)
            )

        obj = get_object_or_404(queryset, **filter_kwargs)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj

    ########################
    ### The following are placeholder methods,
    ### and are intended to be overridden.
    ###
    ### The are not called by GenericAPIView directly,
    ### but are used by the mixin methods.

    def pre_save(self, obj):
        """
        Placeholder method for calling before saving an object.

        May be used to set attributes on the object that are implicit
        in either the request, or the url.
        """
        pass

    def post_save(self, obj, created=False):
        """
        Placeholder method for calling after saving an object.
        """
        pass


##########################################################
### Concrete view classes that provide method handlers ###
### by composing the mixin classes with the base view. ###
##########################################################

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


##########################
### Deprecated classes ###
##########################

class MultipleObjectAPIView(GenericAPIView):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            'Subclassing `MultipleObjectAPIView` is due to be deprecated. '
            'You should simply subclass `GenericAPIView` instead.',
            PendingDeprecationWarning, stacklevel=2
        )
        super(MultipleObjectAPIView, self).__init__(*args, **kwargs)


class SingleObjectAPIView(GenericAPIView):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            'Subclassing `SingleObjectAPIView` is due to be deprecated. '
            'You should simply subclass `GenericAPIView` instead.',
            PendingDeprecationWarning, stacklevel=2
        )
        super(SingleObjectAPIView, self).__init__(*args, **kwargs)
