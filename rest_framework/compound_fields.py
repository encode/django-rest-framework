"""
Compound fields for processing values that are lists and dicts of values described by embedded
fields.
"""
from .fields import WritableField


class ListField(WritableField):
    """
    A field whose values are lists of items described by the given item field. The item field can
    be another field type (e.g., CharField) or a serializer.
    """

    def __init__(self, item_field=None, *args, **kwargs):
        super(ListField, self).__init__(*args, **kwargs)
        self.item_field = item_field

    def to_native(self, obj):
        if self.item_field and obj:
            return [
                self.item_field.to_native(item)
                for item in obj
            ]
        return obj

    def from_native(self, data):
        if self.item_field and data:
            return [
                self.item_field.from_native(item_data)
                for item_data in data
            ]
        return data


class DictField(WritableField):
    """
    A field whose values are dicts of values described by the given value field. The value field
    can be another field type (e.g., CharField) or a serializer.
    """

    def __init__(self, value_field=None, unicode_options=None, *args, **kwargs):
        super(DictField, self).__init__(*args, **kwargs)
        self.value_field = value_field
        self.unicode_options = unicode_options or {}

    def to_native(self, obj):
        if self.value_field and obj:
            return dict(
                (unicode(key, **self.unicode_options), self.value_field.to_native(value))
                for key, value in obj.items()
            )
        return obj

    def from_native(self, data):
        if self.value_field and data:
            return dict(
                (unicode(key, **self.unicode_options), self.value_field.from_native(value))
                for key, value in data.items()
            )
        return data
