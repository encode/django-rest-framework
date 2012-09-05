# Settings

Settings for REST framework are all namespaced in the `API_SETTINGS` setting.
For example your project's `settings.py` file might look like this:

    API_SETTINGS = {
        'DEFAULT_RENDERERS': (
            'djangorestframework.renderers.YAMLRenderer',
        )
        'DEFAULT_PARSERS': (
            'djangorestframework.parsers.YAMLParser',
        )
    }

## DEFAULT_RENDERERS

A list or tuple of renderer classes, that determines the default set of renderers that may be used when returning a `Response` object.

Default:

    (
        'djangorestframework.renderers.JSONRenderer',
        'djangorestframework.renderers.DocumentingHTMLRenderer'
        'djangorestframework.renderers.TemplateHTMLRenderer'
    )

## DEFAULT_PARSERS

A list or tuple of parser classes, that determines the default set of parsers used when accessing the `request.DATA` property.

Default:

    (
        'djangorestframework.parsers.JSONParser',
        'djangorestframework.parsers.FormParser'
    )

## DEFAULT_AUTHENTICATION

A list or tuple of authentication classes, that determines the default set of authenticators used when accessing the `request.user` or `request.auth` properties.

Default if `DEBUG` is `True`:

    (
        'djangorestframework.authentication.SessionAuthentication',
        'djangorestframework.authentication.UserBasicAuthentication'
    )

Default if `DEBUG` is `False`:

    (
        'djangorestframework.authentication.SessionAuthentication',
    )

## DEFAULT_PERMISSIONS

Default: `()`

## DEFAULT_THROTTLES

Default: `()`

## DEFAULT_MODEL_SERIALIZER

Default: `djangorestframework.serializers.ModelSerializer`

## DEFAULT_PAGINATION_SERIALIZER

Default: `djangorestframework.pagination.PaginationSerializer`

## FORMAT_SUFFIX_KWARG

Default: `'format'`

## UNAUTHENTICATED_USER

The class that should be used to initialize `request.user` for unauthenticated requests.

Default: `django.contrib.auth.models.AnonymousUser`

## UNAUTHENTICATED_USER

The class that should be used to initialize `request.auth` for unauthenticated requests.

Default: `None`

## FORM_METHOD_OVERRIDE

The name of a form field that may be used to override the HTTP method of the form.

Default: `'_method'`

## FORM_CONTENT_OVERRIDE

The name of a form field that may be used to override the content of the form payload.

Default: `'_content'`

## FORM_CONTENTTYPE_OVERRIDE

The name of a form field that may be used to override the content type of the form payload.

Default: `'_content_type'`

## URL_ACCEPT_OVERRIDE

The name of a URL parameter that may be used to override the HTTP `Accept` header.

Default: `'_accept'`
