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

## API policy settings

*The following settings control the basic API policies, and are applied to every `APIView` class based view, or `@api_view` function based view.*

#### DEFAULT_RENDERER_CLASSES

A list or tuple of renderer classes, that determines the default set of renderers that may be used when returning a `Response` object.

Default:

    (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    )

#### DEFAULT_PARSER_CLASSES

A list or tuple of parser classes, that determines the default set of parsers used when accessing the `request.DATA` property.

Default:

    (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser'
    )

#### DEFAULT_AUTHENTICATION_CLASSES

A list or tuple of authentication classes, that determines the default set of authenticators used when accessing the `request.user` or `request.auth` properties.

Default:

    (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication'
    )

#### DEFAULT_PERMISSION_CLASSES

A list or tuple of permission classes, that determines the default set of permissions checked at the start of a view.

Default:

    (
        'rest_framework.permissions.AllowAny',
    )

#### DEFAULT_THROTTLE_CLASSES

A list or tuple of throttle classes, that determines the default set of throttles checked at the start of a view.

Default: `()`

#### DEFAULT_CONTENT_NEGOTIATION_CLASS

A content negotiation class, that determines how a renderer is selected for the response, given an incoming request.

Default: `'rest_framework.negotiation.DefaultContentNegotiation'`

---

## Generic view settings

*The following settings control the behavior of the generic class based views.*

#### DEFAULT_MODEL_SERIALIZER_CLASS

A class that determines the default type of model serializer that should be used by a generic view if `model` is specified, but `serializer_class` is not provided.

Default: `'rest_framework.serializers.ModelSerializer'`

#### DEFAULT_PAGINATION_SERIALIZER_CLASS

A class the determines the default serialization style for paginated responses.

Default: `rest_framework.pagination.PaginationSerializer`

#### DEFAULT_FILTER_BACKENDS

A list of filter backend classes that should be used for generic filtering.
If set to `None` then generic filtering is disabled.

#### PAGINATE_BY

The default page size to use for pagination.  If set to `None`, pagination is disabled by default.

Default: `None`

#### PAGINATE_BY_PARAM

The name of a query parameter, which can be used by the client to override the default page size to use for pagination.  If set to `None`, clients may not override the default page size.

Default: `None`

---

## Authentication settings

*The following settings control the behavior of unauthenticated requests.*

#### UNAUTHENTICATED_USER

The class that should be used to initialize `request.user` for unauthenticated requests.

Default: `django.contrib.auth.models.AnonymousUser`

#### UNAUTHENTICATED_TOKEN

The class that should be used to initialize `request.auth` for unauthenticated requests.

Default: `None`

---

## Test settings

*The following settings control the behavior of APIRequestFactory and APIClient*

#### TEST_REQUEST_DEFAULT_FORMAT

The default format that should be used when making test requests.

This should match up with the format of one of the renderer classes in the `TEST_REQUEST_RENDERER_CLASSES` setting.

Default: `'multipart'`

#### TEST_REQUEST_RENDERER_CLASSES

The renderer classes that are supported when building test requests.

The format of any of these renderer classes may be used when contructing a test request, for example: `client.post('/users', {'username': 'jamie'}, format='json')`

Default:

    (
        'rest_framework.renderers.MultiPartRenderer',
        'rest_framework.renderers.JSONRenderer'
    )

---

## Browser overrides

*The following settings provide URL or form-based overrides of the default browser behavior.*

#### FORM_METHOD_OVERRIDE

The name of a form field that may be used to override the HTTP method of the form.

If the value of this setting is `None` then form method overloading will be disabled.

Default: `'_method'`

#### FORM_CONTENT_OVERRIDE

The name of a form field that may be used to override the content of the form payload.  Must be used together with `FORM_CONTENTTYPE_OVERRIDE`.

If either setting is `None` then form content overloading will be disabled.

Default: `'_content'`

#### FORM_CONTENTTYPE_OVERRIDE

The name of a form field that may be used to override the content type of the form payload.  Must be used together with `FORM_CONTENT_OVERRIDE`.

If either setting is `None` then form content overloading will be disabled.

Default: `'_content_type'`

#### URL_ACCEPT_OVERRIDE

The name of a URL parameter that may be used to override the HTTP `Accept` header.

If the value of this setting is `None` then URL accept overloading will be disabled.

Default: `'accept'`

#### URL_FORMAT_OVERRIDE

The name of a URL parameter that may be used to override the default `Accept` header based content negotiation.

Default: `'format'`

---

## Date and time formatting

*The following settings are used to control how date and time representations may be parsed and rendered.*

#### DATETIME_FORMAT

A format string that should be used by default for rendering the output of `DateTimeField` serializer fields.  If `None`, then `DateTimeField` serializer fields will return Python `datetime` objects, and the datetime encoding will be determined by the renderer.

May be any of `None`, `'iso-8601'` or a Python [strftime format][strftime] string.

Default: `None`

#### DATETIME_INPUT_FORMATS

A list of format strings that should be used by default for parsing inputs to `DateTimeField` serializer fields.

May be a list including the string `'iso-8601'` or Python [strftime format][strftime] strings.

Default: `['iso-8601']`

#### DATE_FORMAT

A format string that should be used by default for rendering the output of `DateField` serializer fields.  If `None`, then `DateField` serializer fields will return Python `date` objects, and the date encoding will be determined by the renderer.

May be any of `None`, `'iso-8601'` or a Python [strftime format][strftime] string.

Default: `None`

#### DATE_INPUT_FORMATS

A list of format strings that should be used by default for parsing inputs to `DateField` serializer fields.

May be a list including the string `'iso-8601'` or Python [strftime format][strftime] strings.

Default: `['iso-8601']`

#### TIME_FORMAT

A format string that should be used by default for rendering the output of `TimeField` serializer fields.  If `None`, then `TimeField` serializer fields will return Python `time` objects, and the time encoding will be determined by the renderer.

May be any of `None`, `'iso-8601'` or a Python [strftime format][strftime] string.

Default: `None`

#### TIME_INPUT_FORMATS

A list of format strings that should be used by default for parsing inputs to `TimeField` serializer fields.

May be a list including the string `'iso-8601'` or Python [strftime format][strftime] strings.

Default: `['iso-8601']`

---

## Miscellaneous settings

#### FORMAT_SUFFIX_KWARG

The name of a parameter in the URL conf that may be used to provide a format suffix.

Default: `'format'`

[cite]: http://www.python.org/dev/peps/pep-0020/
[strftime]: http://docs.python.org/2/library/time.html#time.strftime
