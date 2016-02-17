import pytest
from django.test import TestCase

from rest_framework import serializers
from rest_framework.settings import api_settings


class TestMandatoryErrorCodeArgument(TestCase):
    """
    If mandatory error code is enabled in settings, it should prevent throwing
    ValidationError without the code set.
    """
    def setUp(self):
        self.DEFAULT_REQUIRE_ERROR_CODES = api_settings.REQUIRE_ERROR_CODES
        api_settings.REQUIRE_ERROR_CODES = True

    def tearDown(self):
        api_settings.REQUIRE_ERROR_CODES = self.DEFAULT_REQUIRE_ERROR_CODES

    def test_validation_error_requires_code_for_simple_messages(self):
        with pytest.raises(AssertionError):
            serializers.ValidationError("")

    def test_validation_error_requires_no_code_for_structured_errors(self):
        """
        ValidationError can hold a list or dictionary of simple errors, in
        which case the code is no longer meaningful and should not be
        specified.
        """
        with pytest.raises(AssertionError):
            serializers.ValidationError([], code='min_value')

        with pytest.raises(AssertionError):
            serializers.ValidationError({}, code='min_value')

    def test_validation_error_stores_error_code(self):
        exception = serializers.ValidationError("", code='min_value')
        assert exception.code == 'min_value'
