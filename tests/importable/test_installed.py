from django.conf import settings
from tests import importable


def test_installed():
    # ensure that apps can freely import rest_framework.compat
    assert 'tests.importable' in settings.INSTALLED_APPS


def test_imported():
    # ensure that the __init__ hasn't been mucked with
    assert hasattr(importable, 'compat')
