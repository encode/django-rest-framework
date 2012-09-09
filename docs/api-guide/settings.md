<a class="github" href="settings.py"></a>

# Settings

Configuration for REST framework is all namespaced inside the `API_SETTINGS` setting.

For example your project's `settings.py` file might look like this:

    API_SETTINGS = {
        'DEFAULT_RENDERERS': (
            'djangorestframework.renderers.YAMLRenderer',
        )
        'DEFAULT_PARSERS': (
            'djangorestframework.parsers.YAMLParser',
        )
    }

## Accessing settings

If you need to access the values of REST framework's API settings in your project,
you should use the `api_settings` object.  For example.

    from djangorestframework.settings import api_settings
    
    print api_settings.DEFAULT_AUTHENTICATION

The `api_settings` object will check for any user-defined settings, and otherwise fallback to the default values.  Any setting that uses string import paths to refer to a class will automatically import and return the referenced class, instead of the string literal.

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

Default:

    (
        'djangorestframework.authentication.SessionAuthentication',
        'djangorestframework.authentication.UserBasicAuthentication'
    )

## DEFAULT_PERMISSIONS

A list or tuple of permission classes, that determines the default set of permissions checked at the start of a view.

Default: `()`

## DEFAULT_THROTTLES

A list or tuple of throttle classes, that determines the default set of throttles checked at the start of a view.

Default: `()`

## DEFAULT_MODEL_SERIALIZER

**TODO**

Default: `djangorestframework.serializers.ModelSerializer`

## DEFAULT_PAGINATION_SERIALIZER

**TODO**

Default: `djangorestframework.pagination.PaginationSerializer`

## FORMAT_SUFFIX_KWARG

**TODO**

Default: `'format'`

## UNAUTHENTICATED_USER

The class that should be used to initialize `request.user` for unauthenticated requests.

Default: `django.contrib.auth.models.AnonymousUser`

## UNAUTHENTICATED_TOKEN

The class that should be used to initialize `request.auth` for unauthenticated requests.

Default: `None`

## FORM_METHOD_OVERRIDE

The name of a form field that may be used to override the HTTP method of the form.

If the value of this setting is `None` then form method overloading will be disabled.

Default: `'_method'`

## FORM_CONTENT_OVERRIDE

The name of a form field that may be used to override the content of the form payload.  Must be used together with `FORM_CONTENTTYPE_OVERRIDE`.

If either setting is `None` then form content overloading will be disabled.

Default: `'_content'`

## FORM_CONTENTTYPE_OVERRIDE

The name of a form field that may be used to override the content type of the form payload.  Must be used together with `FORM_CONTENT_OVERRIDE`.

If either setting is `None` then form content overloading will be disabled.

Default: `'_content_type'`

## URL_ACCEPT_OVERRIDE

The name of a URL parameter that may be used to override the HTTP `Accept` header.

If the value of this setting is `None` then URL accept overloading will be disabled.

Default: `'_accept'`
