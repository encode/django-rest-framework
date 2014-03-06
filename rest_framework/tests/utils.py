from contextlib import contextmanager
from rest_framework.compat import six
from rest_framework.settings import api_settings


@contextmanager
def temporary_setting(setting, value, module=None):
    """
    Temporarily change value of setting for test.

    Optionally reload given module, useful when module uses value of setting on
    import.
    """
    original_value = getattr(api_settings, setting)
    setattr(api_settings, setting, value)

    if module is not None:
        six.moves.reload_module(module)

    yield

    setattr(api_settings, setting, original_value)

    if module is not None:
        six.moves.reload_module(module)
