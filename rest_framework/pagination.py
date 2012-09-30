from rest_framework import serializers

# TODO: Support URLconf kwarg-style paging


class NextPageField(serializers.Field):
    def to_native(self, value):
        if not value.has_next():
            return None
        page = value.next_page_number()
        request = self.context['request']
        return request.build_absolute_uri('?page=%d' % page)


class PreviousPageField(serializers.Field):
    def to_native(self, value):
        if not value.has_previous():
            return None
        page = value.previous_page_number()
        request = self.context['request']
        return request.build_absolute_uri('?page=%d' % page)


class PaginationSerializer(serializers.Serializer):
    count = serializers.Field(source='paginator.count')
    next = NextPageField(source='*')
    previous = PreviousPageField(source='*')

    def to_native(self, obj):
        """
        Prevent default behaviour of iterating over elements, and serializing
        each in turn.
        """
        return self.convert_object(obj)
