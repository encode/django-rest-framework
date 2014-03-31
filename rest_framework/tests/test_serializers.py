from django.db import models
from django.test import TestCase

from rest_framework.serializers import _resolve_model
from rest_framework.tests.models import BasicModel


class ResolveModelTests(TestCase):
    """
    `_resolve_model` should return a Django model class given the
    provided argument is a Django model class itself, or a properly
    formatted string representation of one.
    """
    def test_resolve_django_model(self):
        resolved_model = _resolve_model(BasicModel)
        self.assertEqual(resolved_model, BasicModel)

    def test_resolve_string_representation(self):
        resolved_model = _resolve_model('tests.BasicModel')
        self.assertEqual(resolved_model, BasicModel)

    def test_resolve_non_django_model(self):
        with self.assertRaises(ValueError):
            _resolve_model(TestCase)

    def test_resolve_improper_string_representation(self):
        with self.assertRaises(ValueError):
            _resolve_model('BasicModel')
