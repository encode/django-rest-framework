"""
Basic building blocks for generic class based views.

We don't bind behaviour to http method handlers yet,
which allows mixin classes to be composed in interesting ways.

Eg. Use mixins to build a Resource class, and have a Router class
    perform the binding of http methods to actions for us.
"""
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response


class CreateModelMixin(object):
    """
    Create a model instance.
    Should be mixed in with any `BaseView`.
    """
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.DATA)
        if serializer.is_valid():
            self.object = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ListModelMixin(object):
    """
    List a queryset.
    Should be mixed in with `MultipleObjectBaseView`.
    """
    empty_error = u"Empty list and '%(class_name)s.allow_empty' is False."

    def list(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()

        # Default is to allow empty querysets.  This can be altered by setting
        # `.allow_empty = False`, to raise 404 errors on empty querysets.
        allow_empty = self.get_allow_empty()
        if not allow_empty and len(self.object_list) == 0:
            error_args = {'class_name': self.__class__.__name__}
            raise Http404(self.empty_error % error_args)

        # Pagination size is set by the `.paginate_by` attribute,
        # which may be `None` to disable pagination.
        page_size = self.get_paginate_by(self.object_list)
        if page_size:
            paginator, page, queryset, is_paginated = self.paginate_queryset(self.object_list, page_size)
            serializer = self.get_pagination_serializer(page)
        else:
            serializer = self.get_serializer(instance=self.object_list)

        return Response(serializer.data)


class RetrieveModelMixin(object):
    """
    Retrieve a model instance.
    Should be mixed in with `SingleObjectBaseView`.
    """
    def retrieve(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(instance=self.object)
        return Response(serializer.data)


class UpdateModelMixin(object):
    """
    Update a model instance.
    Should be mixed in with `SingleObjectBaseView`.
    """
    def update(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except Http404:
            self.object = None

        serializer = self.get_serializer(data=request.DATA, instance=self.object)
        if serializer.is_valid():
            if self.object is None:
                obj = serializer.object
                # TODO: Make ModelSerializers return regular instances,
                # not DeserializedObject
                if hasattr(obj, 'object'):
                    obj = obj.object
                self.update_urlconf_attributes(serializer.object.object)
            self.object = serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update_urlconf_attributes(self, obj):
        """
        When update (re)creates an object, we need to set any attributes that
        are tied to the URLconf.
        """
        pk = self.kwargs.get(self.pk_url_kwarg, None)
        if pk:
            setattr(obj, 'pk', pk)

        slug = self.kwargs.get(self.slug_url_kwarg, None)
        if slug:
            slug_field = self.get_slug_field()
            setattr(obj, slug_field, slug)


class DestroyModelMixin(object):
    """
    Destroy a model instance.
    Should be mixed in with `SingleObjectBaseView`.
    """
    def destroy(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# TODO: Remove MetadataMixin, and implement on APIView.options()
class MetadataMixin(object):
    """
    Return a dicitonary of view metadata.
    Should be mixed in with any `BaseView`.

    This mixin is typically used for the HTTP 'OPTIONS' method.
    """
    def metadata(self, request, *args, **kwargs):
        content = {
            'name': self.get_name(),
            'description': self.get_description(),
            'renders': [renderer.media_type for renderer in self.renderer_classes],
            'parses': [parser.media_type for parser in self.parser_classes],
        }
        #  TODO: Add 'fields', from serializer info.
        # serializer = self.get_serializer()
        # if serializer is not None:
        #     field_name_types = {}
        #     for name, field in form.fields.iteritems():
        #         field_name_types[name] = field.__class__.__name__
        #     content['fields'] = field_name_types
        return Response(content, status=status.HTTP_200_OK)
