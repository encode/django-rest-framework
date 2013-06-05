"""
Basic building blocks for generic class based views.

We don't bind behaviour to http method handlers yet,
which allows mixin classes to be composed in interesting ways.
"""
from __future__ import unicode_literals

from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.request import clone_request
import warnings


def _get_validation_exclusions(obj, pk=None, slug_field=None, lookup_field=None):
    """
    Given a model instance, and an optional pk and slug field,
    return the full list of all other field names on that model.

    For use when performing full_clean on a model instance,
    so we only clean the required fields.
    """
    include = []

    if pk:
        # Pending deprecation
        pk_field = obj._meta.pk
        while pk_field.rel:
            pk_field = pk_field.rel.to._meta.pk
        include.append(pk_field.name)

    if slug_field:
        # Pending deprecation
        include.append(slug_field)

    if lookup_field and lookup_field != 'pk':
        include.append(lookup_field)

    return [field.name for field in obj._meta.fields if field.name not in include]


class CreateModelMixin(object):
    """
    Create a model instance.
    """
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.DATA, files=request.FILES)

        if serializer.is_valid():
            self.pre_save(serializer.object)
            self.object = serializer.save(force_insert=True)
            self.post_save(self.object, created=True)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED,
                            headers=headers)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_success_headers(self, data):
        try:
            return {'Location': data['url']}
        except (TypeError, KeyError):
            return {}


class ListModelMixin(object):
    """
    List a queryset.
    """
    empty_error = "Empty list and '%(class_name)s.allow_empty' is False."

    def list(self, request, *args, **kwargs):
        self.object_list = self.filter_queryset(self.get_queryset())

        # Default is to allow empty querysets.  This can be altered by setting
        # `.allow_empty = False`, to raise 404 errors on empty querysets.
        if not self.allow_empty and not self.object_list:
            warnings.warn(
                'The `allow_empty` parameter is due to be deprecated. '
                'To use `allow_empty=False` style behavior, You should override '
                '`get_queryset()` and explicitly raise a 404 on empty querysets.',
                PendingDeprecationWarning
            )
            class_name = self.__class__.__name__
            error_msg = self.empty_error % {'class_name': class_name}
            raise Http404(error_msg)

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

        if self.object is None:
            created = True
            save_kwargs = {'force_insert': True}
            success_status_code = status.HTTP_201_CREATED
        else:
            created = False
            save_kwargs = {'force_update': True}
            success_status_code = status.HTTP_200_OK

        serializer = self.get_serializer(self.object, data=request.DATA,
                                         files=request.FILES, partial=partial)

        if serializer.is_valid():
            self.pre_save(serializer.object)
            self.object = serializer.save(**save_kwargs)
            self.post_save(self.object, created=created)
            return Response(serializer.data, status=success_status_code)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def get_object_or_none(self):
        try:
            return self.get_object()
        except Http404:
            # If this is a PUT-as-create operation, we need to ensure that
            # we have relevant permissions, as if this was a POST request.
            # This will either raise a PermissionDenied exception,
            # or simply return None
            self.check_permissions(clone_request(self.request, 'POST'))

    def pre_save(self, obj):
        """
        Set any attributes on the object that are implicit in the request.
        """
        # pk and/or slug attributes are implicit in the URL.
        lookup = self.kwargs.get(self.lookup_field, None)
        pk = self.kwargs.get(self.pk_url_kwarg, None)
        slug = self.kwargs.get(self.slug_url_kwarg, None)
        slug_field = slug and self.slug_field or None

        if lookup:
            setattr(obj, self.lookup_field, lookup)

        if pk:
            setattr(obj, 'pk', pk)

        if slug:
            setattr(obj, slug_field, slug)

        # Ensure we clean the attributes so that we don't eg return integer
        # pk using a string representation, as provided by the url conf kwarg.
        if hasattr(obj, 'full_clean'):
            exclude = _get_validation_exclusions(obj, pk, slug_field, self.lookup_field)
            obj.full_clean(exclude)


class DestroyModelMixin(object):
    """
    Destroy a model instance.
    """
    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
