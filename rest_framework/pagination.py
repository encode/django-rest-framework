from rest_framework import serializers

# TODO: Support URLconf kwarg-style paging


class PageField(serializers.Field):
    page_field = 'page'


class NextPageField(PageField):
    """
    Field that returns a link to the next page in paginated results.
    """
    def to_native(self, value):
        if not value.has_next():
            return None
        page = value.next_page_number()
        request = self.context.get('request')
        relative_url = '?%s=%d' % (self.page_field, page)
        if request:
            for field, value in request.QUERY_PARAMS.iteritems():
                if field != self.page_field:
                    relative_url += '&%s=%s' % (field, value)
            return request.build_absolute_uri(relative_url)
        return relative_url


class PreviousPageField(PageField):
    """
    Field that returns a link to the previous page in paginated results.
    """
    def to_native(self, value):
        if not value.has_previous():
            return None
        page = value.previous_page_number()
        request = self.context.get('request')
        relative_url = '?%s=%d' % (self.page_field, page)
        if request:
            for field, value in request.QUERY_PARAMS.iteritems():
                if field != self.page_field:
                    relative_url += '&%s=%s' % (field, value)
            return request.build_absolute_uri(relative_url)
        return relative_url


class PaginationSerializerOptions(serializers.SerializerOptions):
    """
    An object that stores the options that may be provided to a
    pagination serializer by using the inner `Meta` class.

    Accessible on the instance as `serializer.opts`.
    """
    def __init__(self, meta):
        super(PaginationSerializerOptions, self).__init__(meta)
        self.object_serializer_class = getattr(meta, 'object_serializer_class',
                                               serializers.Field)


class BasePaginationSerializer(serializers.Serializer):
    """
    A base class for pagination serializers to inherit from,
    to make implementing custom serializers more easy.
    """
    _options_class = PaginationSerializerOptions
    results_field = 'results'

    def __init__(self, *args, **kwargs):
        """
        Override init to add in the object serializer field on-the-fly.
        """
        super(BasePaginationSerializer, self).__init__(*args, **kwargs)
        results_field = self.results_field
        object_serializer = self.opts.object_serializer_class
        self.fields[results_field] = object_serializer(source='object_list')

    def to_native(self, obj):
        """
        Prevent default behaviour of iterating over elements, and serializing
        each in turn.
        """
        return self.convert_object(obj)


class PaginationSerializer(BasePaginationSerializer):
    """
    A default implementation of a pagination serializer.
    """
    count = serializers.Field(source='paginator.count')
    next = NextPageField(source='*')
    previous = PreviousPageField(source='*')
