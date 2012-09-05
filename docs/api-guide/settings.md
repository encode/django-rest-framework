# Settings

Settings for REST framework are all namespaced in the `API_SETTINGS` setting.
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

## DEFAULT_RENDERERS

A list or tuple of renderer classes.

Default:

    (
    'djangorestframework.renderers.JSONRenderer',
    'djangorestframework.renderers.DocumentingHTMLRenderer')`

## DEFAULT_PARSERS

A list or tuple of parser classes.

Default: `()`
