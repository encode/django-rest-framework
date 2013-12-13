"""
Compound fields for processing values that are lists and dicts of values described by embedded
fields.
"""
from .fields import WritableField
from .serializers import BaseSerializer


def field_or_serializer_from_native(field_or_serializer, data):
    if isinstance(field_or_serializer, BaseSerializer):
        return field_or_serializer.from_native(data, None)
    return field_or_serializer.from_native(data)


class ListField(WritableField):
    """
    A field whose values are lists of items described by the given item field. The item field can
    be another field type (e.g., CharField) or a serializer.
    """

    def __init__(self, item_field=None, *args, **kwargs):
        super(ListField, self).__init__(*args, **kwargs)
        self.item_field = item_field

    def to_native(self, obj):
        if obj:
            return [
                self.item_field.to_native(item) if self.item_field else item
                for item in obj
            ]
        return obj

    def from_native(self, data):
        if data:
            return [
                field_or_serializer_from_native(self.item_field, item_data)
                if self.item_field else item_data
                for item_data in data
            ]
        return data


class DictField(WritableField):
    """
    A field whose values are dicts of values described by the given value field. The value field
    can be another field type (e.g., CharField) or a serializer.
    """

    def __init__(self, value_field=None, *args, **kwargs):
        super(DictField, self).__init__(*args, **kwargs)
        self.value_field = value_field

    def to_native(self, obj):
        if obj:
            return dict(
                (key, self.value_field.to_native(value) if self.value_field else value)
                for key, value in obj.items()
            )
        return obj

    def from_native(self, data):
        if data:
            return dict(
                (
                    unicode(key),
                    field_or_serializer_from_native(self.value_field, value)
                    if self.value_field else value
                )
                for key, value in data.items()
            )
        return data
