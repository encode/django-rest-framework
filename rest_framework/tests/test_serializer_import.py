from django.test import TestCase

from rest_framework import serializers
from rest_framework.tests.accounts.serializers import AccountSerializer


class ImportingModelSerializerTests(TestCase):
    """
    In some situations like, GH #1225, it is possible, especially in
    testing, to import a serializer who's related models have not yet
    been resolved by Django. `AccountSerializer` is an example of such
    a serializer (imported at the top of this file).
    """
    def test_import_model_serializer(self):
        """
        The serializer at the top of this file should have been
        imported successfully, and we should be able to instantiate it.
        """
        self.assertIsInstance(AccountSerializer(), serializers.ModelSerializer)
