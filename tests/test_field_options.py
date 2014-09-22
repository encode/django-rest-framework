from rest_framework import fields
import pytest


class TestFieldOptions:
    def test_required(self):
        """
        By default a field must be included in the input.
        """
        field = fields.IntegerField()
        with pytest.raises(fields.ValidationError) as exc_info:
            field.run_validation()
        assert exc_info.value.messages == ['This field is required.']

    def test_not_required(self):
        """
        If `required=False` then a field may be omitted from the input.
        """
        field = fields.IntegerField(required=False)
        with pytest.raises(fields.SkipField):
            field.run_validation()

    def test_disallow_null(self):
        """
        By default `None` is not a valid input.
        """
        field = fields.IntegerField()
        with pytest.raises(fields.ValidationError) as exc_info:
            field.run_validation(None)
        assert exc_info.value.messages == ['This field may not be null.']

    def test_allow_null(self):
        """
        If `allow_null=True` then `None` is a valid input.
        """
        field = fields.IntegerField(allow_null=True)
        output = field.run_validation(None)
        assert output is None

    def test_disallow_blank(self):
        """
        By default '' is not a valid input.
        """
        field = fields.CharField()
        with pytest.raises(fields.ValidationError) as exc_info:
            field.run_validation('')
        assert exc_info.value.messages == ['This field may not be blank.']

    def test_allow_blank(self):
        """
        If `allow_blank=True` then '' is a valid input.
        """
        field = fields.CharField(allow_blank=True)
        output = field.run_validation('')
        assert output is ''
