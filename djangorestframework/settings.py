"""
Settings for REST framework are all namespaced in the API_SETTINGS setting.
For example your project's `settings.py` file might look like this:

API_SETTINGS = {
    'DEFAULT_RENDERERS': (
        'djangorestframework.renderers.JSONRenderer',
        'djangorestframework.renderers.YAMLRenderer',
    )
    'DEFAULT_PARSERS': (
        'djangorestframework.parsers.JSONParser',
        'djangorestframework.parsers.YAMLParser',
    )
}

"""
from django.conf import settings
from django.utils import importlib
from djangorestframework.compat import yaml


DEFAULTS = {
    'DEFAULT_RENDERERS': (
        'djangorestframework.renderers.JSONRenderer',
        'djangorestframework.renderers.JSONPRenderer',
        'djangorestframework.renderers.DocumentingPlainTextRenderer',
    ),
    'DEFAULT_PARSERS': (
        'djangorestframework.parsers.JSONParser',
        'djangorestframework.parsers.FormParser'
    ),
    'DEFAULT_AUTHENTICATION': (
        'djangorestframework.authentication.SessionAuthentication',
        'djangorestframework.authentication.UserBasicAuthentication'
    ),
    'DEFAULT_PERMISSIONS': (),
    'DEFAULT_THROTTLES': (),
    'UNAUTHENTICATED_USER': 'django.contrib.auth.models.AnonymousUser',
    'UNAUTHENTICATED_TOKEN': None,
    'FORM_METHOD_OVERRIDE': '_method',
    'FORM_CONTENT_OVERRIDE': '_content',
    'FORM_CONTENTTYPE_OVERRIDE': '_content_type',
    'URL_ACCEPT_OVERRIDE': '_accept'
}

if yaml:
    DEFAULTS['DEFAULT_RENDERERS'] += ('djangorestframework.renderers.YAMLRenderer', )


# List of settings that may be in string import notation.
IMPORT_STRINGS = (
    'DEFAULT_RENDERERS',
    'DEFAULT_PARSERS',
    'DEFAULT_AUTHENTICATION',
    'DEFAULT_PERMISSIONS',
    'DEFAULT_THROTTLES',
    'UNAUTHENTICATED_USER',
    'UNAUTHENTICATED_TOKEN'
)


def perform_import(val, setting):
    """
    If the given setting is a string import notation,
    then perform the necessary import or imports.
    """
    if val is None or setting not in IMPORT_STRINGS:
        return val

    if isinstance(val, basestring):
        return import_from_string(val, setting)
    elif isinstance(val, (list, tuple)):
        return [import_from_string(item, setting) for item in val]
    return val


def import_from_string(val, setting):
    """
    Attempt to import a class from a string representation.
    """
    try:
        # Nod to tastypie's use of importlib.
        parts = val.split('.')
        module_path, class_name = '.'.join(parts[:-1]), parts[-1]
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except:
        msg = "Could not import '%s' for API setting '%s'" % (val, setting)
        raise ImportError(msg)


class APISettings(object):
    """
    A settings object, that allows API settings to be accessed as properties.
    For example:

        from djangorestframework.settings import api_settings
        print api_settings.DEFAULT_RENDERERS

    Any setting with string import paths will be resolved.
    """
    def __getattr__(self, attr):
        if attr not in DEFAULTS.keys():
            raise AttributeError("Invalid API setting: '%s'" % attr)

        try:
            # Check if present in user settings
            val = perform_import(settings.API_SETTINGS[attr], attr)
        except (AttributeError, KeyError):
            # Fall back to defaults
            val = perform_import(DEFAULTS[attr], attr)

        # Cache the result
        setattr(self, attr, val)
        return val

api_settings = APISettings()
