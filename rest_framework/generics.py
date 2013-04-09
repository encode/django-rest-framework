"""
Generic views that provide commonly needed behaviour.
"""
from __future__ import unicode_literals
from rest_framework import views, mixins
from rest_framework.settings import api_settings
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.core.paginator import Paginator, InvalidPage
from django.http import Http404
from django.utils.translation import ugettext as _

### Base classes for the generic views ###


class GenericAPIView(views.APIView):
    """
    Base class for all other generic views.
    """

    queryset = None
    serializer_class = None

    filter_backend = api_settings.FILTER_BACKEND
    paginate_by = api_settings.PAGINATE_BY
    paginate_by_param = api_settings.PAGINATE_BY_PARAM
    pagination_serializer_class = api_settings.DEFAULT_PAGINATION_SERIALIZER_CLASS
    allow_empty = True
    page_kwarg = 'page'
    lookup_kwarg = 'pk'

    # Pending deprecation
    model = None
    model_serializer_class = api_settings.DEFAULT_MODEL_SERIALIZER_CLASS
    pk_url_kwarg = 'pk'  # Not provided in Django 1.3
    slug_url_kwarg = 'slug'  # Not provided in Django 1.3
    slug_field = 'slug'

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

    def get_pagination_serializer(self, page=None):
        """
        Return a serializer instance to use with paginated data.
        """
        class SerializerClass(self.pagination_serializer_class):
            class Meta:
                object_serializer_class = self.get_serializer_class()

        pagination_serializer_class = SerializerClass
        context = self.get_serializer_context()
        return pagination_serializer_class(instance=page, context=context)

    def get_paginate_by(self, queryset=None):
        """
        Return the size of pages to use with pagination.

        If `PAGINATE_BY_PARAM` is set it will attempt to get the page size
        from a named query parameter in the url, eg. ?page_size=100

        Otherwise defaults to using `self.paginate_by`.
        """
        if self.paginate_by_param:
            query_params = self.request.QUERY_PARAMS
            try:
                return int(query_params[self.paginate_by_param])
            except (KeyError, ValueError):
                pass

        return self.paginate_by

    def paginate_queryset(self, queryset, page_size, paginator_class=Paginator):
        """
        Paginate a queryset.
        """
        paginator = paginator_class(queryset, page_size, allow_empty_first_page=self.allow_empty)
        page_kwarg = self.page_kwarg
        page = self.kwargs.get(page_kwarg) or self.request.GET.get(page_kwarg) or 1
        try:
            page_number = int(page)
        except ValueError:
            if page == 'last':
                page_number = paginator.num_pages
            else:
                raise Http404(_("Page is not 'last', nor can it be converted to an int."))
        try:
            page = paginator.page(page_number)
            return (paginator, page, page.object_list, page.has_other_pages())
        except InvalidPage as e:
            raise Http404(_('Invalid page (%(page_number)s): %(message)s') % {
                                'page_number': page_number,
                                'message': str(e)
            })

    def filter_queryset(self, queryset):
        """
        Given a queryset, filter it with whichever filter backend is in use.
        """
        if not self.filter_backend:
            return queryset
        backend = self.filter_backend()
        return backend.filter_queryset(self.request, queryset, self)

    ### The following methods provide default implementations
    ### that you may want to override for more complex cases.

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

        # TODO: Deprecation warning
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
            # TODO: Deprecation warning
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

        # Perform the lookup filtering.
        pk = self.kwargs.get(self.pk_url_kwarg, None)
        slug = self.kwargs.get(self.slug_url_kwarg, None)
        lookup = self.kwargs.get(self.lookup_kwarg, None)

        if lookup is not None:
            queryset = queryset.filter(**{self.lookup_kwarg: lookup})
        elif pk is not None:
            # TODO: Deprecation warning
            queryset = queryset.filter(pk=pk)
        elif slug is not None:
            # TODO: Deprecation warning
            queryset = queryset.filter(**{self.slug_field: slug})
        else:
            raise AttributeError("Generic detail view %s must be called with "
                                 "either an object pk or a slug."
                                 % self.__class__.__name__)

        try:
            # Get the single item from the filtered queryset
            obj = queryset.get()
        except ObjectDoesNotExist:
            raise Http404(_("No %(verbose_name)s found matching the query") %
                          {'verbose_name': queryset.model._meta.verbose_name})

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj

    ### The following methods are intended to be overridden.

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


### Concrete view classes that provide method handlers ###
### by composing the mixin classes with the base view. ###

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


### Deprecated classes ###

class MultipleObjectAPIView(GenericAPIView):
    pass


class SingleObjectAPIView(GenericAPIView):
    pass
