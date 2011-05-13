"""Tests for the resource module"""
from django.test import TestCase
from djangorestframework.resources import _object_to_data

import datetime
import decimal

class TestObjectToData(TestCase): 
    """Tests for the _object_to_data function"""

    def test_decimal(self):
        """Decimals need to be converted to a string representation."""
        self.assertEquals(_object_to_data(decimal.Decimal('1.5')), '1.5')

    def test_function(self):
        """Functions with no arguments should be called."""
        def foo():
            return 1
        self.assertEquals(_object_to_data(foo), 1)

    def test_method(self):
        """Methods with only a ``self`` argument should be called."""
        class Foo(object):
            def foo(self):
                return 1
        self.assertEquals(_object_to_data(Foo().foo), 1)

    def test_datetime(self):
        """datetime objects are left as-is."""
        now = datetime.datetime.now()
        self.assertEquals(_object_to_data(now), now)