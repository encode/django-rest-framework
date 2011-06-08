"""Tests for the resource module"""
from django.test import TestCase
from djangorestframework.resources import _object_to_data

from django.db import models

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
    
    def test_tuples(self):
        """ Test tuple serialisation """
        class M1(models.Model):
            field1 = models.CharField()
            field2 = models.CharField()
        
        class M2(models.Model):
            field = models.OneToOneField(M1)
        
        class M3(models.Model):
            field = models.ForeignKey(M1)
        
        m1 = M1(field1='foo', field2='bar')
        m2 = M2(field=m1)
        m3 = M3(field=m1)
        
        Resource = type('Resource', (object,), {'fields':(), 'include':(), 'exclude':()})
        
        r = Resource()
        r.fields = (('field', ('field1')),)

        self.assertEqual(_object_to_data(m2, r), dict(field=dict(field1=u'foo')))
        
        r.fields = (('field', ('field2')),)
        self.assertEqual(_object_to_data(m3, r), dict(field=dict(field2=u'bar')))
        
