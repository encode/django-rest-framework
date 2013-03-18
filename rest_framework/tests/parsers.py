from __future__ import unicode_literals
from rest_framework.compat import StringIO
from django import forms
from django.test import TestCase
from django.utils import unittest
from rest_framework.compat import etree
from rest_framework.parsers import FormParser
from rest_framework.parsers import XMLParser
import datetime


class Form(forms.Form):
    field1 = forms.CharField(max_length=3)
    field2 = forms.CharField()


class TestFormParser(TestCase):
    def setUp(self):
        self.string = "field1=abc&field2=defghijk"

    def test_parse(self):
        """ Make sure the `QueryDict` works OK """
        parser = FormParser()

        stream = StringIO(self.string)
        data = parser.parse(stream)

        self.assertEqual(Form(data).is_valid(), True)


class TestXMLParser(TestCase):
    def setUp(self):
        self._input = StringIO(
            '<?xml version="1.0" encoding="utf-8"?>'
            '<root>'
            '<field_a>121.0</field_a>'
            '<field_b>dasd</field_b>'
            '<field_c></field_c>'
            '<field_d>2011-12-25 12:45:00</field_d>'
            '</root>'
        )
        self._data = {
            'field_a': 121,
            'field_b': 'dasd',
            'field_c': None,
            'field_d': datetime.datetime(2011, 12, 25, 12, 45, 00)
        }
        self._complex_data_input = StringIO(
            '<?xml version="1.0" encoding="utf-8"?>'
            '<root>'
            '<creation_date>2011-12-25 12:45:00</creation_date>'
            '<sub_data_list>'
            '<list-item><sub_id>1</sub_id><sub_name>first</sub_name></list-item>'
            '<list-item><sub_id>2</sub_id><sub_name>second</sub_name></list-item>'
            '</sub_data_list>'
            '<name>name</name>'
            '</root>'
        )
        self._complex_data = {
            "creation_date": datetime.datetime(2011, 12, 25, 12, 45, 00),
            "name": "name",
            "sub_data_list": [
                {
                    "sub_id": 1,
                    "sub_name": "first"
                },
                {
                    "sub_id": 2,
                    "sub_name": "second"
                }
            ]
        }

    @unittest.skipUnless(etree, 'defusedxml not installed')
    def test_parse(self):
        parser = XMLParser()
        data = parser.parse(self._input)
        self.assertEqual(data, self._data)

    @unittest.skipUnless(etree, 'defusedxml not installed')
    def test_complex_data_parse(self):
        parser = XMLParser()
        data = parser.parse(self._complex_data_input)
        self.assertEqual(data, self._complex_data)
