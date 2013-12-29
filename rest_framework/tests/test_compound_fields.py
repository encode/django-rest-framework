"""
General serializer field tests.
"""


from datetime import date
import unittest

from django.core.exceptions import ValidationError

from rest_framework import ISO_8601
from rest_framework.compound_fields import DictField
from rest_framework.compound_fields import ListField
from rest_framework.fields import CharField
from rest_framework.fields import DateField


class ListFieldTests(unittest.TestCase):
    """
    Tests for the ListField behavior
    """

    def test_from_native_no_item_field(self):
        """
        When a ListField has no item-field, from_native should return the data it was given
        un-processed.
        """
        field = ListField()
        data = range(5)
        obj = field.from_native(data)
        self.assertEqual(data, obj)

    def test_to_native_no_item_field(self):
        """
        When a ListField has no item-field, to_native should return the data it was given
        un-processed.
        """
        field = ListField()
        obj = range(5)
        data = field.to_native(obj)
        self.assertEqual(obj, data)

    def test_from_native_with_item_field(self):
        """
        When a ListField has an item-field, from_native should return a list of elements resulting
        from the application of the item-field's from_native method to each element of the input
        data list.
        """
        field = ListField(DateField())
        data = ["2000-01-01", "2000-01-02"]
        obj = field.from_native(data)
        self.assertEqual([date(2000, 1, 1), date(2000, 1, 2)], obj)

    def test_to_native_with_item_field(self):
        """
        When a ListField has an item-field, to_native should return a list of elements resulting
        from the application of the item-field's to_native method to each element of the input
        object list.
        """
        field = ListField(DateField(format=ISO_8601))
        obj = [date(2000, 1, 1), date(2000, 1, 2)]
        data = field.to_native(obj)
        self.assertEqual(["2000-01-01", "2000-01-02"], data)

    def test_missing_required_list(self):
        """
        When a ListField requires a value, then validate will raise a ValidationError on a missing
        (None) value.
        """
        field = ListField()
        with self.assertRaises(ValidationError):
            field.validate(None)

    def test_validate_non_list(self):
        """
        When a ListField is given a non-list value, then validate will raise a ValidationError.
        """
        field = ListField()
        with self.assertRaises(ValidationError):
            field.validate('notAList')

    def test_validate_empty_list(self):
        """
        When a ListField requires a value, then validate will raise a ValidationError on an empty
        value.
        """
        field = ListField()
        with self.assertRaises(ValidationError):
            field.validate([])

    def test_validate_elements_valid(self):
        """
        When a ListField is given a list whose elements are valid for the item-field, then validate
        will not raise a ValidationError.
        """
        field = ListField(CharField(max_length=5))
        try:
            field.validate(["a", "b", "c"])
        except ValidationError:
            self.fail("ValidationError was raised")

    def test_validate_elements_invalid(self):
        """
        When a ListField is given a list containing elements that are invalid for the item-field,
        then validate will raise a ValidationError.
        """
        field = ListField(CharField(max_length=5))
        with self.assertRaises(ValidationError):
            field.validate(["012345", "012345"])


class DictFieldTests(unittest.TestCase):
    """
    Tests for the DictField behavior
    """

    def test_from_native_no_value_field(self):
        """
        When a DictField has no value-field, from_native should return the data it was given
        un-processed.
        """
        field = DictField()
        data = {"a": 1, "b": 2}
        obj = field.from_native(data)
        self.assertEqual(data, obj)

    def test_to_native_no_value_field(self):
        """
        When a DictField has no value-field, to_native should return the data it was given
        un-processed.
        """
        field = DictField()
        obj = {"a": 1, "b": 2}
        data = field.to_native(obj)
        self.assertEqual(obj, data)

    def test_from_native_with_value_field(self):
        """
        When a DictField has an value-field, from_native should return a dict of elements resulting
        from the application of the value-field's from_native method to each value of the input
        data dict.
        """
        field = DictField(DateField())
        data = {"a": "2000-01-01", "b": "2000-01-02"}
        obj = field.from_native(data)
        self.assertEqual({"a": date(2000, 1, 1), "b": date(2000, 1, 2)}, obj)

    def test_to_native_with_value_field(self):
        """
        When a DictField has an value-field, to_native should return a dict of elements resulting
        from the application of the value-field's to_native method to each value of the input
        object dict.
        """
        field = DictField(DateField(format=ISO_8601))
        obj = {"a": date(2000, 1, 1), "b": date(2000, 1, 2)}
        data = field.to_native(obj)
        self.assertEqual({"a": "2000-01-01", "b": "2000-01-02"}, data)

    def test_missing_required_dict(self):
        """
        When a DictField requires a value, then validate will raise a ValidationError on a missing
        (None) value.
        """
        field = DictField()
        with self.assertRaises(ValidationError):
            field.validate(None)

    def test_validate_non_dict(self):
        """
        When a DictField is given a non-dict value, then validate will raise a ValidationError.
        """
        field = DictField()
        with self.assertRaises(ValidationError):
            field.validate('notADict')

    def test_validate_empty_dict(self):
        """
        When a DictField requires a value, then validate will raise a ValidationError on an empty
        value.
        """
        field = DictField()
        with self.assertRaises(ValidationError):
            field.validate({})

    def test_validate_elements_valid(self):
        """
        When a DictField is given a dict whose values are valid for the value-field, then validate
        will not raise a ValidationError.
        """
        field = DictField(CharField(max_length=5))
        try:
            field.validate({"a": "a", "b": "b", "c": "c"})
        except ValidationError:
            self.fail("ValidationError was raised")

    def test_validate_elements_invalid(self):
        """
        When a DictField is given a dict containing values that are invalid for the value-field,
        then validate will raise a ValidationError.
        """
        field = DictField(CharField(max_length=5))
        with self.assertRaises(ValidationError):
            field.validate({"a": "012345", "b": "012345"})
