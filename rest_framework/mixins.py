"""
Basic building blocks for generic class based views.

We don't bind behaviour to http method handlers yet,
which allows mixin classes to be composed in interesting ways.
"""
from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.request import clone_request
from rest_framework.settings import api_settings


def _get_validation_exclusions(obj, lookup_field=None):
    """
    Given a model instance, and an optional pk and slug field,
    return the full list of all other field names on that model.

    For use when performing full_clean on a model instance,
    so we only clean the required fields.
    """
    if lookup_field == 'pk':
        pk_field = obj._meta.pk
        while pk_field.rel:
            pk_field = pk_field.rel.to._meta.pk
        lookup_field = pk_field.name

    return [field.name for field in obj._meta.fields if field.name != lookup_field]


class CreateModelMixin(object):
    """
    Create a model instance.
    """
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.DATA)

        if serializer.is_valid():
            self.object = serializer.save()
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED,
                            headers=headers)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_success_headers(self, data):
        try:
            return {'Location': data[api_settings.URL_FIELD_NAME]}
        except (TypeError, KeyError):
            return {}


class ListModelMixin(object):
    """
    List a queryset.
    """
    def list(self, request, *args, **kwargs):
        self.object_list = self.filter_queryset(self.get_queryset())

        # Switch between paginated or standard style responses
        page = self.paginate_queryset(self.object_list)
        if page is not None:
            serializer = self.get_pagination_serializer(page)
        else:
            serializer = self.get_serializer(self.object_list, many=True)

        return Response(serializer.data)


class RetrieveModelMixin(object):
    """
    Retrieve a model instance.
    """
    def retrieve(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(self.object)
        return Response(serializer.data)


class UpdateModelMixin(object):
    """
    Update a model instance.
    """
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        self.object = self.get_object_or_none()

        serializer = self.get_serializer(self.object, data=request.DATA, partial=partial)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.kwargs[lookup_url_kwarg]
        extras = {self.lookup_field: lookup_value}

        if self.object is None:
            self.object = serializer.save(extras=extras)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        self.object = serializer.save(extras=extras)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def get_object_or_none(self):
        try:
            return self.get_object()
        except Http404:
            if self.request.method == 'PUT':
                # For PUT-as-create operation, we need to ensure that we have
                # relevant permissions, as if this was a POST request.  This
                # will either raise a PermissionDenied exception, or simply
                # return None.
                self.check_permissions(clone_request(self.request, 'POST'))
            else:
                # PATCH requests where the object does not exist should still
                # return a 404 response.
                raise

    def pre_save(self, obj):
        """
        Set any attributes on the object that are implicit in the request.
        """
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.kwargs[lookup_url_kwarg]

        setattr(obj, self.lookup_field, lookup_value)

        # Ensure we clean the attributes so that we don't eg return integer
        # pk using a string representation, as provided by the url conf kwarg.
        if hasattr(obj, 'full_clean'):
            exclude = _get_validation_exclusions(obj, self.lookup_field)
            obj.full_clean(exclude)


class DestroyModelMixin(object):
    """
    Destroy a model instance.
    """
    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        self.pre_delete(obj)
        obj.delete()
        self.post_delete(obj)
        return Response(status=status.HTTP_204_NO_CONTENT)
