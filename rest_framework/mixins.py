"""
Basic building blocks for generic class based views.

We don't bind behaviour to http method handlers yet,
which allows mixin classes to be composed in interesting ways.
"""
from __future__ import unicode_literals

import warnings

from rest_framework import status
from rest_framework.response import Response
from rest_framework.settings import api_settings

class CreateOrUpdateHooksMixin(object):
    def __init__(self, *args, **kwargs):
        warnings.warn('The pre_save and post_save hooks are deprecated. Use perform_create and perform_update instead.',
                      PendingDeprecationWarning, stacklevel=2)
        super(CreateOrUpdateHooksMixin, self).__init__(*args, **kwargs)
    
    def pre_save(obj):
        pass
    
    def perform_create(self, serializer):
        self.pre_save(serializer.instance)
        instance = serializer.save() 
        self.post_save(instance, created=True)
        
    def perform_update(self, serializer):
        self.pre_save(serializer.instance)
        instance = serializer.save() 
        self.post_save(instance, created=False)
    
    def post_save(obj, created=False):
        pass
    
class DeleteHooksMixin(object):
    def __init__(self, *args, **kwargs):
        warnings.warn('The pre_delete and post_delete hooks are deprecated. Use perform_delete instead.',
                      PendingDeprecationWarning, stacklevel=2)
        super(DeleteHooksMixin, self).__init__(*args, **kwargs)
    
    def pre_delete(obj):
        pass
    
    def perform_delete(self, instance):
        self.pre_delete(instance)
        instance.delete()
        self.post_delete(instance)
        
    def post_delete(obj):
        pass
        

class CreateModelMixin(object):
    """
    Create a model instance.
    """
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save()

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
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class RetrieveModelMixin(object):
    """
    Retrieve a model instance.
    """
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class UpdateModelMixin(object):
    """
    Update a model instance.
    """
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def perform_update(self, serializer):
        serializer.save()

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


class DestroyModelMixin(object):
    """
    Destroy a model instance.
    """
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.delete()
