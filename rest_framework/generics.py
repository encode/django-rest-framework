"""
Generic views that provide commonly needed behaviour.
"""

from rest_framework import views, mixins
from rest_framework.settings import api_settings
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.list import MultipleObjectMixin


### Base classes for the generic views ###

class GenericAPIView(views.APIView):
    """
    Base class for all other generic views.
    """
    serializer_class = None
    model_serializer_class = api_settings.DEFAULT_MODEL_SERIALIZER_CLASS

    def get_serializer_context(self):
        """
        Extra context provided to the serializer class.
        """
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }

    def get_serializer_class(self):
        """
        Return the class to use for the serializer.
        Use `self.serializer_class`, falling back to constructing a
        model serializer class from `self.model_serializer_class`
        """
        serializer_class = self.serializer_class

        if serializer_class is None:
            class DefaultSerializer(self.model_serializer_class):
                class Meta:
                    model = self.model
            serializer_class = DefaultSerializer

        return serializer_class

    def get_serializer(self, instance=None, data=None, files=None):
        # TODO: add support for files
        # TODO: add support for seperate serializer/deserializer
        serializer_class = self.get_serializer_class()
        context = self.get_serializer_context()
        return serializer_class(instance, data=data, context=context)


class MultipleObjectAPIView(MultipleObjectMixin, GenericAPIView):
    """
    Base class for generic views onto a queryset.
    """

    pagination_serializer_class = api_settings.DEFAULT_PAGINATION_SERIALIZER_CLASS
    paginate_by = api_settings.PAGINATE_BY
    filter_backend = api_settings.FILTER_BACKEND

    def filter_queryset(self, queryset):
        if not self.filter_backend:
            return queryset
        backend = self.filter_backend()
        return backend.filter_queryset(self.request, queryset, self)

    def get_filtered_queryset(self):
        return self.filter_queryset(self.get_queryset())

    def get_pagination_serializer_class(self):
        """
        Return the class to use for the pagination serializer.
        """
        class SerializerClass(self.pagination_serializer_class):
            class Meta:
                object_serializer_class = self.get_serializer_class()

        return SerializerClass

    def get_pagination_serializer(self, page=None):
        pagination_serializer_class = self.get_pagination_serializer_class()
        context = self.get_serializer_context()
        return pagination_serializer_class(instance=page, context=context)


class SingleObjectAPIView(SingleObjectMixin, GenericAPIView):
    """
    Base class for generic views onto a model instance.
    """
    pk_url_kwarg = 'pk'  # Not provided in Django 1.3
    slug_url_kwarg = 'slug'  # Not provided in Django 1.3

    def get_object(self):
        """
        Override default to add support for object-level permissions.
        """
        obj = super(SingleObjectAPIView, self).get_object()
        if not self.has_permission(self.request, obj):
            self.permission_denied(self.request)
        return obj


### Concrete view classes that provide method handlers ###
### by composing the mixin classes with a base view.   ###


class CreateAPIView(mixins.CreateModelMixin,
                    GenericAPIView):

    """
    Concrete view for creating a model instance.
    """
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class ListAPIView(mixins.ListModelMixin,
                  MultipleObjectAPIView):
    """
    Concrete view for listing a queryset.
    """
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class RetrieveAPIView(mixins.RetrieveModelMixin,
                      SingleObjectAPIView):
    """
    Concrete view for retrieving a model instance.
    """
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class DestroyAPIView(mixins.DestroyModelMixin,
                     SingleObjectAPIView):

    """
    Concrete view for deleting a model instance.
    """
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class UpdateAPIView(mixins.UpdateModelMixin,
                    SingleObjectAPIView):

    """
    Concrete view for updating a model instance.
    """
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class ListCreateAPIView(mixins.ListModelMixin,
                        mixins.CreateModelMixin,
                        MultipleObjectAPIView):
    """
    Concrete view for listing a queryset or creating a model instance.
    """
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class RetrieveDestroyAPIView(mixins.RetrieveModelMixin,
                             mixins.DestroyModelMixin,
                             SingleObjectAPIView):
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
                                   SingleObjectAPIView):
    """
    Concrete view for retrieving, updating or deleting a model instance.
    """
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
