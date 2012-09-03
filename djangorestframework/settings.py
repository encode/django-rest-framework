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
from djangorestframework import renderers
from djangorestframework.compat import yaml


DEFAULTS = {
    'DEFAULT_RENDERERS': (
        renderers.JSONRenderer,
        renderers.JSONPRenderer,
        renderers.DocumentingHTMLRenderer,
        renderers.DocumentingXHTMLRenderer,
        renderers.DocumentingPlainTextRenderer,
        renderers.XMLRenderer
    )
}

if yaml:
    DEFAULTS['DEFAULT_RENDERERS'] += (renderers.YAMLRenderer, )


class APISettings(object):
    def __getattr__(self, attr):
        try:
            return settings.API_SETTINGS[attr]
        except (AttributeError, KeyError):
            # 'API_SETTINGS' does not exist,
            # or requested setting is not present in 'API_SETTINGS'.
            try:
                return DEFAULTS[attr]
            except KeyError:
                raise AttributeError("No such setting '%s'" % attr)

api_settings = APISettings()
