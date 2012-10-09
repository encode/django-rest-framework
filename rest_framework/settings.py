"""
Settings for REST framework are all namespaced in the REST_FRAMEWORK setting.
For example your project's `settings.py` file might look like this:

REST_FRAMEWORK = {
    'DEFAULT_RENDERERS': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.YAMLRenderer',
    )
    'DEFAULT_PARSERS': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.YAMLParser',
    )
}

This module provides the `api_setting` object, that is used to access
REST framework settings, checking for user settings first, then falling
back to the defaults.
"""
from django.conf import settings
from django.utils import importlib


DEFAULTS = {
    'DEFAULT_RENDERERS': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'DEFAULT_PARSERS': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser'
    ),
    'DEFAULT_AUTHENTICATION': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.UserBasicAuthentication'
    ),
    'DEFAULT_PERMISSIONS': (),
    'DEFAULT_THROTTLES': (),
    'DEFAULT_CONTENT_NEGOTIATION':
        'rest_framework.negotiation.DefaultContentNegotiation',
    'DEFAULT_THROTTLE_RATES': {
        'user': None,
        'anon': None,
    },

    'MODEL_SERIALIZER': 'rest_framework.serializers.ModelSerializer',
    'PAGINATION_SERIALIZER': 'rest_framework.pagination.PaginationSerializer',
    'PAGINATE_BY': None,

    'UNAUTHENTICATED_USER': 'django.contrib.auth.models.AnonymousUser',
    'UNAUTHENTICATED_TOKEN': None,

    'FORM_METHOD_OVERRIDE': '_method',
    'FORM_CONTENT_OVERRIDE': '_content',
    'FORM_CONTENTTYPE_OVERRIDE': '_content_type',
    'URL_ACCEPT_OVERRIDE': 'accept',
    'URL_FORMAT_OVERRIDE': 'format',

    'FORMAT_SUFFIX_KWARG': 'format'
}


# List of settings that may be in string import notation.
IMPORT_STRINGS = (
    'DEFAULT_RENDERERS',
    'DEFAULT_PARSERS',
    'DEFAULT_AUTHENTICATION',
    'DEFAULT_PERMISSIONS',
    'DEFAULT_THROTTLES',
    'DEFAULT_CONTENT_NEGOTIATION',
    'MODEL_SERIALIZER',
    'PAGINATION_SERIALIZER',
    'UNAUTHENTICATED_USER',
    'UNAUTHENTICATED_TOKEN',
)


def perform_import(val, setting):
    """
    If the given setting is a string import notation,
    then perform the necessary import or imports.
    """
    if val is None or not setting in IMPORT_STRINGS:
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

        from rest_framework.settings import api_settings
        print api_settings.DEFAULT_RENDERERS

    Any setting with string import paths will be automatically resolved
    and return the class, rather than the string literal.
    """
    def __getattr__(self, attr):
        if attr not in DEFAULTS.keys():
            raise AttributeError("Invalid API setting: '%s'" % attr)

        try:
            # Check if present in user settings
            val = perform_import(settings.REST_FRAMEWORK[attr], attr)
        except (AttributeError, KeyError):
            # Fall back to defaults
            val = perform_import(DEFAULTS[attr], attr)

        # Cache the result
        setattr(self, attr, val)
        return val

api_settings = APISettings()
