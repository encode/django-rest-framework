"""
Generic views that provide commmonly needed behaviour.
"""

from rest_framework import views, mixins, serializers
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.list import MultipleObjectMixin


### Base classes for the generic views ###

class BaseView(views.APIView):
    """
    Base class for all other generic views.
    """
    serializer_class = None

    def get_serializer(self, data=None, files=None, instance=None):
        # TODO: add support for files
        # TODO: add support for seperate serializer/deserializer
        serializer_class = self.serializer_class

        if serializer_class is None:
            class DefaultSerializer(serializers.ModelSerializer):
                class Meta:
                    model = self.model
            serializer_class = DefaultSerializer

        context = {
            'request': self.request,
            'format': self.kwargs.get('format', None)
        }
        return serializer_class(data, instance=instance, context=context)


class MultipleObjectBaseView(MultipleObjectMixin, BaseView):
    """
    Base class for generic views onto a queryset.
    """
    pass


class SingleObjectBaseView(SingleObjectMixin, BaseView):
    """
    Base class for generic views onto a model instance.
    """

    def get_object(self):
        """
        Override default to add support for object-level permissions.
        """
        obj = super(SingleObjectBaseView, self).get_object()
        if not self.has_permission(self.request, obj):
            self.permission_denied(self.request)
        return obj


### Concrete view classes that provide method handlers ###
### by composing the mixin classes with a base view.   ###

class ListAPIView(mixins.ListModelMixin,
                  mixins.MetadataMixin,
                  MultipleObjectBaseView):
    """
    Concrete view for listing a queryset.
    """
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def options(self, request, *args, **kwargs):
        return self.metadata(request, *args, **kwargs)


class RootAPIView(mixins.ListModelMixin,
                  mixins.CreateModelMixin,
                  mixins.MetadataMixin,
                  MultipleObjectBaseView):
    """
    Concrete view for listing a queryset or creating a model instance.
    """
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def options(self, request, *args, **kwargs):
        return self.metadata(request, *args, **kwargs)


class DetailAPIView(mixins.RetrieveModelMixin,
                    mixins.MetadataMixin,
                    SingleObjectBaseView):
    """
    Concrete view for retrieving a model instance.
    """
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def options(self, request, *args, **kwargs):
        return self.metadata(request, *args, **kwargs)


class InstanceAPIView(mixins.RetrieveModelMixin,
                      mixins.UpdateModelMixin,
                      mixins.DestroyModelMixin,
                      mixins.MetadataMixin,
                      SingleObjectBaseView):
    """
    Concrete view for retrieving, updating or deleting a model instance.
    """
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

    def options(self, request, *args, **kwargs):
        return self.metadata(request, *args, **kwargs)
