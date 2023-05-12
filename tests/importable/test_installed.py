from django.conf import settings

from tests import importable


def test_installed():
    # ensure the test app hasn't been removed from the test suite
    assert 'tests.importable' in settings.INSTALLED_APPS


def test_compat():
    assert hasattr(importable, 'compat')


def test_serializer_fields_initialization():
    assert hasattr(importable, 'ExampleSerializer')

    serializer = importable.ExampleSerializer()
    assert 'charfield' in serializer.fields
    assert 'integerfield' in serializer.fields
    assert 'floatfield' in serializer.fields
    assert 'decimalfield' in serializer.fields
    assert 'durationfield' in serializer.fields
    assert 'listfield' in serializer.fields
