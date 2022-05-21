---
source:
    - settings.py
---

# Settings

> Namespaces are one honking great idea - let's do more of those!
>
> &mdash; [The Zen of Python][cite]

Configuration for REST framework is all namespaced inside a single Django setting, named `REST_FRAMEWORK`.

For example your project's `settings.py` file might include something like this:

    REST_FRAMEWORK = {
        'DEFAULT_RENDERER_CLASSES': [
            'rest_framework.renderers.JSONRenderer',
        ],
        'DEFAULT_PARSER_CLASSES': [
            'rest_framework.parsers.JSONParser',
        ]
    }

## Accessing settings

If you need to access the values of REST framework's API settings in your project,
you should use the `api_settings` object.  For example.

    from rest_framework.settings import api_settings

    print(api_settings.DEFAULT_AUTHENTICATION_CLASSES)

The `api_settings` object will check for any user-defined settings, and otherwise fall back to the default values.  Any setting that uses string import paths to refer to a class will automatically import and return the referenced class, instead of the string literal.

---

# API Reference

## API policy settings

*The following settings control the basic API policies, and are applied to every `APIView` class-based view, or `@api_view` function based view.*

#### DEFAULT_RENDERER_CLASSES

A list or tuple of renderer classes, that determines the default set of renderers that may be used when returning a `Response` object.

Default:

    [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ]

#### DEFAULT_PARSER_CLASSES

A list or tuple of parser classes, that determines the default set of parsers used when accessing the `request.data` property.

Default:

    [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser'
    ]

#### DEFAULT_AUTHENTICATION_CLASSES

A list or tuple of authentication classes, that determines the default set of authenticators used when accessing the `request.user` or `request.auth` properties.

Default:

    [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication'
    ]

#### DEFAULT_PERMISSION_CLASSES

A list or tuple of permission classes, that determines the default set of permissions checked at the start of a view. Permission must be granted by every class in the list.

Default:

    [
        'rest_framework.permissions.AllowAny',
    ]

#### DEFAULT_THROTTLE_CLASSES

A list or tuple of throttle classes, that determines the default set of throttles checked at the start of a view.

Default: `[]`

#### DEFAULT_CONTENT_NEGOTIATION_CLASS

A content negotiation class, that determines how a renderer is selected for the response, given an incoming request.

Default: `'rest_framework.negotiation.DefaultContentNegotiation'`

#### DEFAULT_SCHEMA_CLASS

A view inspector class that will be used for schema generation.

Default: `'rest_framework.schemas.openapi.AutoSchema'`

---

## Generic view settings

*The following settings control the behavior of the generic class-based views.*

#### DEFAULT_FILTER_BACKENDS

A list of filter backend classes that should be used for generic filtering.
If set to `None` then generic filtering is disabled.

#### DEFAULT_PAGINATION_CLASS

The default class to use for queryset pagination. If set to `None`, pagination
is disabled by default. See the pagination documentation for further guidance on
[setting](pagination.md#setting-the-pagination-style) and
[modifying](pagination.md#modifying-the-pagination-style) the pagination style.

Default: `None`

#### PAGE_SIZE

The default page size to use for pagination.  If set to `None`, pagination is disabled by default.

Default: `None`

### SEARCH_PARAM

The name of a query parameter, which can be used to specify the search term used by `SearchFilter`.

Default: `search`

#### ORDERING_PARAM

The name of a query parameter, which can be used to specify the ordering of results returned by `OrderingFilter`.

Default: `ordering`

---

## Versioning settings

#### DEFAULT_VERSION

The value that should be used for `request.version` when no versioning information is present.

Default: `None`

#### ALLOWED_VERSIONS

If set, this value will restrict the set of versions that may be returned by the versioning scheme, and will raise an error if the provided version if not in this set.

Default: `None`

#### VERSION_PARAM

The string that should used for any versioning parameters, such as in the media type or URL query parameters.

Default: `'version'`

---

## Authentication settings

*The following settings control the behavior of unauthenticated requests.*

#### UNAUTHENTICATED_USER

The class that should be used to initialize `request.user` for unauthenticated requests.
(If removing authentication entirely, e.g. by removing `django.contrib.auth` from
`INSTALLED_APPS`, set `UNAUTHENTICATED_USER` to `None`.)

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

The format of any of these renderer classes may be used when constructing a test request, for example: `client.post('/users', {'username': 'jamie'}, format='json')`

Default:

    [
        'rest_framework.renderers.MultiPartRenderer',
        'rest_framework.renderers.JSONRenderer'
    ]

---

## Schema generation controls

#### SCHEMA_COERCE_PATH_PK

If set, this maps the `'pk'` identifier in the URL conf onto the actual field
name when generating a schema path parameter. Typically this will be `'id'`.
This gives a more suitable representation as "primary key" is an implementation
detail, whereas "identifier" is a more general concept.

Default: `True`

#### SCHEMA_COERCE_METHOD_NAMES

If set, this is used to map internal viewset method names onto external action
names used in the schema generation. This allows us to generate names that
are more suitable for an external representation than those that are used
internally in the codebase.

Default: `{'retrieve': 'read', 'destroy': 'delete'}`

---

## Content type controls

#### URL_FORMAT_OVERRIDE

The name of a URL parameter that may be used to override the default content negotiation `Accept` header behavior, by using a `format=…` query parameter in the request URL.

For example: `http://example.com/organizations/?format=csv`

If the value of this setting is `None` then URL format overrides will be disabled.

Default: `'format'`

#### FORMAT_SUFFIX_KWARG

The name of a parameter in the URL conf that may be used to provide a format suffix. This setting is applied when using `format_suffix_patterns` to include suffixed URL patterns.

For example: `http://example.com/organizations.csv/`

Default: `'format'`

---

## Date and time formatting

*The following settings are used to control how date and time representations may be parsed and rendered.*

#### DATETIME_FORMAT

A format string that should be used by default for rendering the output of `DateTimeField` serializer fields.  If `None`, then `DateTimeField` serializer fields will return Python `datetime` objects, and the datetime encoding will be determined by the renderer.

May be any of `None`, `'iso-8601'` or a Python [strftime format][strftime] string.

Default: `'iso-8601'`

#### DATETIME_INPUT_FORMATS

A list of format strings that should be used by default for parsing inputs to `DateTimeField` serializer fields.

May be a list including the string `'iso-8601'` or Python [strftime format][strftime] strings.

Default: `['iso-8601']`

#### DATE_FORMAT

A format string that should be used by default for rendering the output of `DateField` serializer fields.  If `None`, then `DateField` serializer fields will return Python `date` objects, and the date encoding will be determined by the renderer.

May be any of `None`, `'iso-8601'` or a Python [strftime format][strftime] string.

Default: `'iso-8601'`

#### DATE_INPUT_FORMATS

A list of format strings that should be used by default for parsing inputs to `DateField` serializer fields.

May be a list including the string `'iso-8601'` or Python [strftime format][strftime] strings.

Default: `['iso-8601']`

#### TIME_FORMAT

A format string that should be used by default for rendering the output of `TimeField` serializer fields.  If `None`, then `TimeField` serializer fields will return Python `time` objects, and the time encoding will be determined by the renderer.

May be any of `None`, `'iso-8601'` or a Python [strftime format][strftime] string.

Default: `'iso-8601'`

#### TIME_INPUT_FORMATS

A list of format strings that should be used by default for parsing inputs to `TimeField` serializer fields.

May be a list including the string `'iso-8601'` or Python [strftime format][strftime] strings.

Default: `['iso-8601']`

---

## Encodings

#### UNICODE_JSON

When set to `True`, JSON responses will allow unicode characters in responses. For example:

    {"unicode black star":"★"}

When set to `False`, JSON responses will escape non-ascii characters, like so:

    {"unicode black star":"\u2605"}

Both styles conform to [RFC 4627][rfc4627], and are syntactically valid JSON. The unicode style is preferred as being more user-friendly when inspecting API responses.

Default: `True`

#### COMPACT_JSON

When set to `True`, JSON responses will return compact representations, with no spacing after `':'` and `','` characters. For example:

    {"is_admin":false,"email":"jane@example"}

When set to `False`, JSON responses will return slightly more verbose representations, like so:

    {"is_admin": false, "email": "jane@example"}

The default style is to return minified responses, in line with [Heroku's API design guidelines][heroku-minified-json].

Default: `True`

#### STRICT_JSON

When set to `True`, JSON rendering and parsing will only observe syntactically valid JSON, raising an exception for the extended float values (`nan`, `inf`, `-inf`) accepted by Python's `json` module. This is the recommended setting, as these values are not generally supported. e.g., neither Javascript's `JSON.Parse` nor PostgreSQL's JSON data type accept these values.

When set to `False`, JSON rendering and parsing will be permissive. However, these values are still invalid and will need to be specially handled in your code.

Default: `True`

#### COERCE_DECIMAL_TO_STRING

When returning decimal objects in API representations that do not support a native decimal type, it is normally best to return the value as a string. This avoids the loss of precision that occurs with binary floating point implementations.

When set to `True`, the serializer `DecimalField` class will return strings instead of `Decimal` objects. When set to `False`, serializers will return `Decimal` objects, which the default JSON encoder will return as floats.

Default: `True`

---

## View names and descriptions

**The following settings are used to generate the view names and descriptions, as used in responses to `OPTIONS` requests, and as used in the browsable API.**

#### VIEW_NAME_FUNCTION

A string representing the function that should be used when generating view names.

This should be a function with the following signature:

    view_name(self)

* `self`: The view instance.  Typically the name function would inspect the name of the class when generating a descriptive name, by accessing `self.__class__.__name__`.

If the view instance inherits `ViewSet`, it may have been initialized with several optional arguments:

* `name`: A name explicitly provided to a view in the viewset. Typically, this value should be used as-is when provided.
* `suffix`: Text used when differentiating individual views in a viewset. This argument is mutually exclusive to `name`.
* `detail`: Boolean that differentiates an individual view in a viewset as either being a 'list' or 'detail' view.

Default: `'rest_framework.views.get_view_name'`

#### VIEW_DESCRIPTION_FUNCTION

A string representing the function that should be used when generating view descriptions.

This setting can be changed to support markup styles other than the default markdown.  For example, you can use it to support `rst` markup in your view docstrings being output in the browsable API.

This should be a function with the following signature:

    view_description(self, html=False)

* `self`: The view instance.  Typically the description function would inspect the docstring of the class when generating a description, by accessing `self.__class__.__doc__`
* `html`: A boolean indicating if HTML output is required.  `True` when used in the browsable API, and `False` when used in generating `OPTIONS` responses.

If the view instance inherits `ViewSet`, it may have been initialized with several optional arguments:

* `description`: A description explicitly provided to the view in the viewset. Typically, this is set by extra viewset `action`s, and should be used as-is.

Default: `'rest_framework.views.get_view_description'`

## HTML Select Field cutoffs

Global settings for [select field cutoffs for rendering relational fields](relations.md#select-field-cutoffs) in the browsable API.

#### HTML_SELECT_CUTOFF

Global setting for the `html_cutoff` value.  Must be an integer.

Default: 1000

#### HTML_SELECT_CUTOFF_TEXT

A string representing a global setting for `html_cutoff_text`.

Default: `"More than {count} items..."`

---

## Miscellaneous settings

#### EXCEPTION_HANDLER

A string representing the function that should be used when returning a response for any given exception.  If the function returns `None`, a 500 error will be raised.

This setting can be changed to support error responses other than the default `{"detail": "Failure..."}` responses.  For example, you can use it to provide API responses like `{"errors": [{"message": "Failure...", "code": ""} ...]}`.

This should be a function with the following signature:

    exception_handler(exc, context)

* `exc`: The exception.

Default: `'rest_framework.views.exception_handler'`

#### NON_FIELD_ERRORS_KEY

A string representing the key that should be used for serializer errors that do not refer to a specific field, but are instead general errors.

Default: `'non_field_errors'`

#### URL_FIELD_NAME

A string representing the key that should be used for the URL fields generated by `HyperlinkedModelSerializer`.

Default: `'url'`

#### NUM_PROXIES

An integer of 0 or more, that may be used to specify the number of application proxies that the API runs behind.  This allows throttling to more accurately identify client IP addresses.  If set to `None` then less strict IP matching will be used by the throttle classes.

Default: `None`

[cite]: https://www.python.org/dev/peps/pep-0020/
[rfc4627]: https://www.ietf.org/rfc/rfc4627.txt
[heroku-minified-json]: https://github.com/interagent/http-api-design#keep-json-minified-in-all-responses
[strftime]: https://docs.python.org/3/library/time.html#time.strftime
