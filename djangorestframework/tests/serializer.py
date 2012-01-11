"""Tests for the resource module"""
from django.db import models
from django.test import TestCase
from django.utils.translation import ugettext_lazy
from djangorestframework.serializer import Serializer

import datetime
import decimal

class TestObjectToData(TestCase):
    """
    Tests for the Serializer class.
    """

    def setUp(self):
        self.serializer = Serializer()
        self.serialize = self.serializer.serialize

    def test_decimal(self):
        """Decimals need to be converted to a string representation."""
        self.assertEquals(self.serialize(decimal.Decimal('1.5')), decimal.Decimal('1.5'))

    def test_function(self):
        """Functions with no arguments should be called."""
        def foo():
            return 1
        self.assertEquals(self.serialize(foo), 1)

    def test_method(self):
        """Methods with only a ``self`` argument should be called."""
        class Foo(object):
            def foo(self):
                return 1
        self.assertEquals(self.serialize(Foo().foo), 1)

    def test_datetime(self):
        """datetime objects are left as-is."""
        now = datetime.datetime.now()
        self.assertEquals(self.serialize(now), now)

    def test_dict_method_name_collision(self):
        """dict with key that collides with dict method name"""
        self.assertEquals(self.serialize({'items': 'foo'}), {'items': u'foo'})
        self.assertEquals(self.serialize({'keys': 'foo'}), {'keys': u'foo'})
        self.assertEquals(self.serialize({'values': 'foo'}), {'values': u'foo'})

    def test_ugettext_lazy(self):
        self.assertEquals(self.serialize(ugettext_lazy('foobar')), u'foobar')


class TestFieldNesting(TestCase):
    """
    Test nesting the fields in the Serializer class
    """
    def setUp(self):
        self.serializer = Serializer()
        self.serialize = self.serializer.serialize

        class M1(models.Model):
            field1 = models.CharField(max_length=256)
            field2 = models.CharField(max_length=256)

        class M2(models.Model):
            field = models.OneToOneField(M1)

        class M3(models.Model):
            field = models.ForeignKey(M1)

        self.m1 = M1(field1='foo', field2='bar')
        self.m2 = M2(field=self.m1)
        self.m3 = M3(field=self.m1)


    def test_tuple_nesting(self):
        """
        Test tuple nesting on `fields` attr
        """
        class SerializerM2(Serializer):
            fields = (('field', ('field1',)),)

        class SerializerM3(Serializer):
            fields = (('field', ('field2',)),)

        self.assertEqual(SerializerM2().serialize(self.m2), {'field': {'field1': u'foo'}})
        self.assertEqual(SerializerM3().serialize(self.m3), {'field': {'field2': u'bar'}})


    def test_serializer_class_nesting(self):
        """
        Test related model serialization
        """
        class NestedM2(Serializer):
            fields = ('field1', )

        class NestedM3(Serializer):
            fields = ('field2', )

        class SerializerM2(Serializer):
            fields = [('field', NestedM2)]

        class SerializerM3(Serializer):
            fields = [('field', NestedM3)]

        self.assertEqual(SerializerM2().serialize(self.m2), {'field': {'field1': u'foo'}})
        self.assertEqual(SerializerM3().serialize(self.m3), {'field': {'field2': u'bar'}})

    def test_serializer_classname_nesting(self):
        """
        Test related model serialization
        """
        class SerializerM2(Serializer):
            fields = [('field', 'NestedM2')]

        class SerializerM3(Serializer):
            fields = [('field', 'NestedM3')]

        class NestedM2(Serializer):
            fields = ('field1', )

        class NestedM3(Serializer):
            fields = ('field2', )

        self.assertEqual(SerializerM2().serialize(self.m2), {'field': {'field1': u'foo'}})
        self.assertEqual(SerializerM3().serialize(self.m3), {'field': {'field2': u'bar'}})

    def test_serializer_overridden_hook_method(self):
        """
        Test serializing a model instance which overrides a class method on the
        serializer.  Checks for correct behaviour in odd edge case.
        """
        class SerializerM2(Serializer):
            fields = ('overridden', )

            def overridden(self):
                return False

        self.m2.overridden = True
        self.assertEqual(SerializerM2().serialize_model(self.m2),
                         {'overridden': True})
