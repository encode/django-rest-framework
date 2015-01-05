"""
Pagination serializers determine the structure of the output that should
be used for paginated responses.
"""
from __future__ import unicode_literals
from rest_framework import serializers
from rest_framework.templatetags.rest_framework import replace_query_param


class NextPageField(serializers.Field):
    """
    Field that returns a link to the next page in paginated results.
    """
    page_field = 'page'

    def to_representation(self, value):
        if not value.has_next():
            return None
        page = value.next_page_number()
        request = self.context.get('request')
        url = request and request.build_absolute_uri() or ''
        return replace_query_param(url, self.page_field, page)


class PreviousPageField(serializers.Field):
    """
    Field that returns a link to the previous page in paginated results.
    """
    page_field = 'page'

    def to_representation(self, value):
        if not value.has_previous():
            return None
        page = value.previous_page_number()
        request = self.context.get('request')
        url = request and request.build_absolute_uri() or ''
        return replace_query_param(url, self.page_field, page)


class DefaultObjectSerializer(serializers.Serializer):
    """
    If no object serializer is specified, then this serializer will be applied
    as the default.
    """
    def to_representation(self, value):
        return value


class BasePaginationSerializer(serializers.Serializer):
    """
    A base class for pagination serializers to inherit from,
    to make implementing custom serializers more easy.
    """
    results_field = 'results'

    def __init__(self, *args, **kwargs):
        """
        Override init to add in the object serializer field on-the-fly.
        """
        super(BasePaginationSerializer, self).__init__(*args, **kwargs)
        results_field = self.results_field

        try:
            object_serializer = self.Meta.object_serializer_class
        except AttributeError:
            object_serializer = DefaultObjectSerializer

        try:
            list_serializer_class = object_serializer.Meta.list_serializer_class
        except AttributeError:
            list_serializer_class = serializers.ListSerializer

        self.fields[results_field] = list_serializer_class(
            child=object_serializer(*args, **kwargs),
            source='object_list'
        )


class PaginationSerializer(BasePaginationSerializer):
    """
    A default implementation of a pagination serializer.
    """
    count = serializers.ReadOnlyField(source='paginator.count')
    next = NextPageField(source='*')
    previous = PreviousPageField(source='*')
