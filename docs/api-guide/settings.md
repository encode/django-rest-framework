<a class="github" href="settings.py"></a>

# Settings

> Namespaces are one honking great idea - let's do more of those!
>
> &mdash; [The Zen of Python][cite]

Configuration for REST framework is all namespaced inside a single Django setting, named `REST_FRAMEWORK`.

For example your project's `settings.py` file might include something like this:

    REST_FRAMEWORK = {
        'DEFAULT_RENDERER_CLASSES': (
            'rest_framework.renderers.YAMLRenderer',
        ),
        'DEFAULT_PARSER_CLASSES': (
            'rest_framework.parsers.YAMLParser',
        )
    }

## Accessing settings

If you need to access the values of REST framework's API settings in your project,
you should use the `api_settings` object.  For example.

    from rest_framework.settings import api_settings
    
    print api_settings.DEFAULT_AUTHENTICATION_CLASSES

The `api_settings` object will check for any user-defined settings, and otherwise fallback to the default values.  Any setting that uses string import paths to refer to a class will automatically import and return the referenced class, instead of the string literal.

---

# API Reference

## DEFAULT_RENDERER_CLASSES

A list or tuple of renderer classes, that determines the default set of renderers that may be used when returning a `Response` object.

Default:

    (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
        'rest_framework.renderers.TemplateHTMLRenderer'
    )

## DEFAULT_PARSER_CLASSES

A list or tuple of parser classes, that determines the default set of parsers used when accessing the `request.DATA` property.

Default:

    (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser'
    )

## DEFAULT_AUTHENTICATION_CLASSES

A list or tuple of authentication classes, that determines the default set of authenticators used when accessing the `request.user` or `request.auth` properties.

Default:

    (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.UserBasicAuthentication'
    )

## DEFAULT_PERMISSION_CLASSES

A list or tuple of permission classes, that determines the default set of permissions checked at the start of a view.

Default:

    (
        'rest_framework.permissions.AllowAny',
    )

## DEFAULT_THROTTLE_CLASSES

A list or tuple of throttle classes, that determines the default set of throttles checked at the start of a view.

Default: `()`

## DEFAULT_MODEL_SERIALIZER_CLASS

**TODO**

Default: `rest_framework.serializers.ModelSerializer`

## DEFAULT_PAGINATION_SERIALIZER_CLASS

**TODO**

Default: `rest_framework.pagination.PaginationSerializer`

## FILTER_BACKEND

The filter backend class that should be used for generic filtering.  If set to `None` then generic filtering is disabled.

## PAGINATE_BY

The default page size to use for pagination.  If set to `None`, pagination is disabled by default.

Default: `None`

## PAGINATE_BY_KWARG

The name of a query parameter, which can be used by the client to overide the default page size to use for pagination.  If set to `None`, clients may not override the default page size.

Default: `None`

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

Default: `'accept'`

## URL_FORMAT_OVERRIDE

Default: `'format'`

## FORMAT_SUFFIX_KWARG

**TODO**

Default: `'format'`

[cite]: http://www.python.org/dev/peps/pep-0020/
