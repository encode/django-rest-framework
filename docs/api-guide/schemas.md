source: schemas.py

# Schemas

> A machine-readable [schema] describes what resources are available via the API, what their URLs are, how they are represented and what operations they support.
>
> &mdash; Heroku, [JSON Schema for the Heroku Platform API][cite]

API schemas are a useful tool that allow for a range of use cases, including
generating reference documentation, or driving dynamic client libraries that
can interact with your API.

## Install Core API

You'll need to install the `coreapi` package in order to add schema support
for REST framework.

    pip install coreapi

## Internal schema representation

REST framework uses [Core API][coreapi] in order to model schema information in
a format-independent representation. This information can then be rendered
into various different schema formats, or used to generate API documentation.

When using Core API, a schema is represented as a `Document` which is the
top-level container object for information about the API. Available API
interactions are represented using `Link` objects. Each link includes a URL,
HTTP method, and may include a list of `Field` instances, which describe any
parameters that may be accepted by the API endpoint. The `Link` and `Field`
instances may also include descriptions, that allow an API schema to be
rendered into user documentation.

Here's an example of an API description that includes a single `search`
endpoint:

    coreapi.Document(
        title='Flight Search API',
        url='https://api.example.org/',
        content={
            'search': coreapi.Link(
                url='/search/',
                action='get',
                fields=[
                    coreapi.Field(
                        name='from',
                        required=True,
                        location='query',
                        description='City name or airport code.'
                    ),
                    coreapi.Field(
                        name='to',
                        required=True,
                        location='query',
                        description='City name or airport code.'
                    ),
                    coreapi.Field(
                        name='date',
                        required=True,
                        location='query',
                        description='Flight date in "YYYY-MM-DD" format.'
                    )
                ],
                description='Return flight availability and prices.'
            )
        }
    )

## Schema output formats

In order to be presented in an HTTP response, the internal representation
has to be rendered into the actual bytes that are used in the response.

[Core JSON][corejson] is designed as a canonical format for use with Core API.
REST framework includes a renderer class for handling this media type, which
is available as `renderers.CoreJSONRenderer`.

### Alternate schema formats

Other schema formats such as [Open API][open-api] ("Swagger"),
[JSON HyperSchema][json-hyperschema], or [API Blueprint][api-blueprint] can also
be supported by implementing a custom renderer class that handles converting a
`Document` instance into a bytestring representation.

If there is a Core API codec package that supports encoding into the format you
want to use then implementing the renderer class can be done by using the codec.

#### Example

For example, the `openapi_codec` package provides support for encoding or decoding
to the Open API ("Swagger") format:

    from rest_framework import renderers
    from openapi_codec import OpenAPICodec

    class SwaggerRenderer(renderers.BaseRenderer):
        media_type = 'application/openapi+json'
        format = 'swagger'

        def render(self, data, media_type=None, renderer_context=None):
            codec = OpenAPICodec()
            return codec.dump(data)




## Schemas vs Hypermedia

It's worth pointing out here that Core API can also be used to model hypermedia
responses, which present an alternative interaction style to API schemas.

With an API schema, the entire available interface is presented up-front
as a single endpoint. Responses to individual API endpoints are then typically
presented as plain data, without any further interactions contained in each
response.

With Hypermedia, the client is instead presented with a document containing
both data and available interactions. Each interaction results in a new
document, detailing both the current state and the available interactions.

Further information and support on building Hypermedia APIs with REST framework
is planned for a future version.


---

# Creating a schema

REST framework includes functionality for auto-generating a schema,
or allows you to specify one explicitly.

## Manual Schema Specification

To manually specify a schema you create a Core API `Document`, similar to the
example above.

    schema = coreapi.Document(
        title='Flight Search API',
        content={
            ...
        }
    )


## Automatic Schema Generation

Automatic schema generation is provided by the `SchemaGenerator` class.

`SchemaGenerator` processes a list of routed URL pattterns and compiles the
appropriately structured Core API Document.

Basic usage is just to provide the title for your schema and call
`get_schema()`:

    generator = schemas.SchemaGenerator(title='Flight Search API')
    schema = generator.get_schema()

## Per-View Schema Customisation

By default, view introspection is performed by an `AutoSchema` instance
accessible via the `schema` attribute on `APIView`. This provides the
appropriate Core API `Link` object for the view, request method and path:

    auto_schema = view.schema
    coreapi_link = auto_schema.get_link(...)

(In compiling the schema, `SchemaGenerator` calls `view.schema.get_link()` for
each view, allowed method and path.)

To customise the `Link` generation you may:

* Instantiate `AutoSchema` on your view with the `manual_fields` kwarg:

        from rest_framework.views import APIView
        from rest_framework.schemas import AutoSchema

        class CustomView(APIView):
            ...
            schema = AutoSchema(
                manual_fields=[
                    coreapi.Field("extra_field", ...),
                ]
            )

    This allows extension for the most common case without subclassing.

* Provide an `AutoSchema` subclass with more complex customisation:

        from rest_framework.views import APIView
        from rest_framework.schemas import AutoSchema

        class CustomSchema(AutoSchema):
            def get_link(...):
                # Implement custom introspection here (or in other sub-methods)

        class CustomView(APIView):
            ...
            schema = CustomSchema()

    This provides complete control over view introspection.

* Instantiate `ManualSchema` on your view, providing the Core API `Fields` for
  the view explicitly:

        from rest_framework.views import APIView
        from rest_framework.schemas import ManualSchema

        class CustomView(APIView):
            ...
            schema = ManualSchema(fields=[
                coreapi.Field(
                    "first_field",
                    required=True,
                    location="path",
                    schema=coreschema.String()
                ),
                coreapi.Field(
                    "second_field",
                    required=True,
                    location="path",
                    schema=coreschema.String()
                ),
            ])

    This allows manually specifying the schema for some views whilst maintaining
    automatic generation elsewhere.

You may disable schema generation for a view by setting `schema` to `None`:

        class CustomView(APIView):
            ...
            schema = None  # Will not appear in schema

---

**Note**: For full details on `SchemaGenerator` plus the `AutoSchema` and
`ManualSchema` descriptors see the [API Reference below](#api-reference).

---

# Adding a schema view

There are a few different ways to add a schema view to your API, depending on
exactly what you need.

## The get_schema_view shortcut

The simplest way to include a schema in your project is to use the
`get_schema_view()` function.

    from rest_framework.schemas import get_schema_view

    schema_view = get_schema_view(title="Server Monitoring API")

    urlpatterns = [
        url('^$', schema_view),
        ...
    ]

Once the view has been added, you'll be able to make API requests to retrieve
the auto-generated schema definition.

    $ http http://127.0.0.1:8000/ Accept:application/coreapi+json
    HTTP/1.0 200 OK
    Allow: GET, HEAD, OPTIONS
    Content-Type: application/vnd.coreapi+json

    {
        "_meta": {
            "title": "Server Monitoring API"
        },
        "_type": "document",
        ...
    }

The arguments to `get_schema_view()` are:

#### `title`

May be used to provide a descriptive title for the schema definition.

#### `url`

May be used to pass a canonical URL for the schema.

    schema_view = get_schema_view(
        title='Server Monitoring API',
        url='https://www.example.org/api/'
    )

#### `urlconf`

A string representing the import path to the URL conf that you want
to generate an API schema for. This defaults to the value of Django's
ROOT_URLCONF setting.

    schema_view = get_schema_view(
        title='Server Monitoring API',
        url='https://www.example.org/api/',
        urlconf='myproject.urls'
    )

#### `renderer_classes`

May be used to pass the set of renderer classes that can be used to render the API root endpoint.

    from rest_framework.schemas import get_schema_view
    from rest_framework.renderers import CoreJSONRenderer
    from my_custom_package import APIBlueprintRenderer

    schema_view = get_schema_view(
        title='Server Monitoring API',
        url='https://www.example.org/api/',
        renderer_classes=[CoreJSONRenderer, APIBlueprintRenderer]
    )

#### `patterns`

List of url patterns to limit the schema introspection to. If you only want the `myproject.api` urls
to be exposed in the schema:

    schema_url_patterns = [
        url(r'^api/', include('myproject.api.urls')),
    ]

    schema_view = get_schema_view(
        title='Server Monitoring API',
        url='https://www.example.org/api/',
        patterns=schema_url_patterns,
    )

#### `generator_class`

May be used to specify a `SchemaGenerator` subclass to be passed to the
`SchemaView`.

#### `authentication_classes`

May be used to specify the list of authentication classes that will apply to the schema endpoint.
Defaults to `settings.DEFAULT_AUTHENTICATION_CLASSES`

#### `permission_classes`

May be used to specify the list of permission classes that will apply to the schema endpoint.
Defaults to `settings.DEFAULT_PERMISSION_CLASSES`


## Using an explicit schema view

If you need a little more control than the `get_schema_view()` shortcut gives you,
then you can use the `SchemaGenerator` class directly to auto-generate the
`Document` instance, and to return that from a view.

This option gives you the flexibility of setting up the schema endpoint
with whatever behaviour you want. For example, you can apply different
permission, throttling, or authentication policies to the schema endpoint.

Here's an example of using `SchemaGenerator` together with a view to
return the schema.

**views.py:**

    from rest_framework.decorators import api_view, renderer_classes
    from rest_framework import renderers, response, schemas

    generator = schemas.SchemaGenerator(title='Bookings API')

    @api_view()
    @renderer_classes([renderers.CoreJSONRenderer])
    def schema_view(request):
        schema = generator.get_schema(request)
        return response.Response(schema)

**urls.py:**

    urlpatterns = [
        url('/', schema_view),
        ...
    ]

You can also serve different schemas to different users, depending on the
permissions they have available. This approach can be used to ensure that
unauthenticated requests are presented with a different schema to
authenticated requests, or to ensure that different parts of the API are
made visible to different users depending on their role.

In order to present a schema with endpoints filtered by user permissions,
you need to pass the `request` argument to the `get_schema()` method, like so:

    @api_view()
    @renderer_classes([renderers.CoreJSONRenderer])
    def schema_view(request):
        generator = schemas.SchemaGenerator(title='Bookings API')
        return response.Response(generator.get_schema(request=request))

## Explicit schema definition

An alternative to the auto-generated approach is to specify the API schema
explicitly, by declaring a `Document` object in your codebase. Doing so is a
little more work, but ensures that you have full control over the schema
representation.

    import coreapi
    from rest_framework.decorators import api_view, renderer_classes
    from rest_framework import renderers, response

    schema = coreapi.Document(
        title='Bookings API',
        content={
            ...
        }
    )

    @api_view()
    @renderer_classes([renderers.CoreJSONRenderer])
    def schema_view(request):
        return response.Response(schema)

## Static schema file

A final option is to write your API schema as a static file, using one
of the available formats, such as Core JSON or Open API.

You could then either:

* Write a schema definition as a static file, and [serve the static file directly][static-files].
* Write a schema definition that is loaded using `Core API`, and then
  rendered to one of many available formats, depending on the client request.

---

# Schemas as documentation

One common usage of API schemas is to use them to build documentation pages.

The schema generation in REST framework uses docstrings to automatically
populate descriptions in the schema document.

These descriptions will be based on:

* The corresponding method docstring if one exists.
* A named section within the class docstring, which can be either single line or multi-line.
* The class docstring.

## Examples

An `APIView`, with an explicit method docstring.

    class ListUsernames(APIView):
        def get(self, request):
            """
            Return a list of all user names in the system.
            """
            usernames = [user.username for user in User.objects.all()]
            return Response(usernames)

A `ViewSet`, with an explict action docstring.

    class ListUsernames(ViewSet):
        def list(self, request):
            """
            Return a list of all user names in the system.
            """
            usernames = [user.username for user in User.objects.all()]
            return Response(usernames)

A generic view with sections in the class docstring, using single-line style.

    class UserList(generics.ListCreateAPIView):
        """
        get: List all the users.
        post: Create a new user.
        """
        queryset = User.objects.all()
        serializer_class = UserSerializer
        permission_classes = (IsAdminUser,)

A generic viewset with sections in the class docstring, using multi-line style.

    class UserViewSet(viewsets.ModelViewSet):
        """
        API endpoint that allows users to be viewed or edited.

        retrieve:
        Return a user instance.

        list:
        Return all users, ordered by most recently joined.
        """
        queryset = User.objects.all().order_by('-date_joined')
        serializer_class = UserSerializer

---

# API Reference

## SchemaGenerator

A class that walks a list of routed URL patterns, requests the schema for each view,
and collates the resulting CoreAPI Document.

Typically you'll instantiate `SchemaGenerator` with a single argument, like so:

    generator = SchemaGenerator(title='Stock Prices API')

Arguments:

* `title` **required** - The name of the API.
* `url` - The root URL of the API schema. This option is not required unless the schema is included under path prefix.
* `patterns` - A list of URLs to inspect when generating the schema. Defaults to the project's URL conf.
* `urlconf` - A URL conf module name to use when generating the schema. Defaults to `settings.ROOT_URLCONF`.

### get_schema(self, request)

Returns a `coreapi.Document` instance that represents the API schema.

    @api_view
    @renderer_classes([renderers.CoreJSONRenderer])
    def schema_view(request):
        generator = schemas.SchemaGenerator(title='Bookings API')
        return Response(generator.get_schema())

The `request` argument is optional, and may be used if you want to apply per-user
permissions to the resulting schema generation.

### get_links(self, request)

Return a nested dictionary containing all the links that should be included in the API schema.

This is a good point to override if you want to modify the resulting structure of the generated schema,
as you can build a new dictionary with a different layout.


## AutoSchema

A class that deals with introspection of individual views for schema generation.

`AutoSchema` is attached to `APIView` via the `schema` attribute.

The `AutoSchema` constructor takes a single keyword argument  `manual_fields`.

**`manual_fields`**: a `list` of `coreapi.Field` instances that will be added to
the generated fields. Generated fields with a matching `name` will be overwritten.

    class CustomView(APIView):
        schema = AutoSchema(manual_fields=[
            coreapi.Field(
                "my_extra_field",
                required=True,
                location="path",
                schema=coreschema.String()
            ),
        ])

For more advanced customisation subclass `AutoSchema` to customise schema generation.

    class CustomViewSchema(AutoSchema):
        """
        Overrides `get_link()` to provide Custom Behavior X
        """

        def get_link(self, path, method, base_url):
            link = super().get_link(path, method, base_url)
            # Do something to customize link here...
            return link

    class MyView(APIView):
      schema = CustomViewSchema()

The following methods are available to override.

### get_link(self, path, method, base_url)

Returns a `coreapi.Link` instance corresponding to the given view.

This is the main entry point.
You can override this if you need to provide custom behaviors for particular views.

### get_description(self, path, method)

Returns a string to use as the link description. By default this is based on the
view docstring as described in the "Schemas as Documentation" section above.

### get_encoding(self, path, method)

Returns a string to indicate the encoding for any request body, when interacting
with the given view. Eg. `'application/json'`. May return a blank string for views
that do not expect a request body.

### get_path_fields(self, path, method):

Return a list of `coreapi.Link()` instances. One for each path parameter in the URL.

### get_serializer_fields(self, path, method)

Return a list of `coreapi.Link()` instances. One for each field in the serializer class used by the view.

### get_pagination_fields(self, path, method)

Return a list of `coreapi.Link()` instances, as returned by the `get_schema_fields()` method on any pagination class used by the view.

### get_filter_fields(self, path, method)

Return a list of `coreapi.Link()` instances, as returned by the `get_schema_fields()` method of any filter classes used by the view.


## ManualSchema

Allows manually providing a list of `coreapi.Field` instances for the schema,
plus an optional description.

    class MyView(APIView):
      schema = ManualSchema(fields=[
            coreapi.Field(
                "first_field",
                required=True,
                location="path",
                schema=coreschema.String()
            ),
            coreapi.Field(
                "second_field",
                required=True,
                location="path",
                schema=coreschema.String()
            ),
        ]
      )

The `ManualSchema` constructor takes two arguments:

**`fields`**: A list of `coreapi.Field` instances. Required.

**`description`**: A string description. Optional.

---

## Core API

This documentation gives a brief overview of the components within the `coreapi`
package that are used to represent an API schema.

Note that these classes are imported from the `coreapi` package, rather than
from the `rest_framework` package.

### Document

Represents a container for the API schema.

#### `title`

A name for the API.

#### `url`

A canonical URL for the API.

#### `content`

A dictionary, containing the `Link` objects that the schema contains.

In order to provide more structure to the schema, the `content` dictionary
may be nested, typically to a second level. For example:

    content={
        "bookings": {
            "list": Link(...),
            "create": Link(...),
            ...
        },
        "venues": {
            "list": Link(...),
            ...
        },
        ...
    }

### Link

Represents an individual API endpoint.

#### `url`

The URL of the endpoint. May be a URI template, such as `/users/{username}/`.

#### `action`

The HTTP method associated with the endpoint. Note that URLs that support
more than one HTTP method, should correspond to a single `Link` for each.

#### `fields`

A list of `Field` instances, describing the available parameters on the input.

#### `description`

A short description of the meaning and intended usage of the endpoint.

### Field

Represents a single input parameter on a given API endpoint.

#### `name`

A descriptive name for the input.

#### `required`

A boolean, indicated if the client is required to included a value, or if
the parameter can be omitted.

#### `location`

Determines how the information is encoded into the request. Should be one of
the following strings:

**"path"**

Included in a templated URI. For example a `url` value of `/products/{product_code}/` could be used together with a `"path"` field, to handle API inputs in a URL path such as `/products/slim-fit-jeans/`.

These fields will normally correspond with [named arguments in the project URL conf][named-arguments].

**"query"**

Included as a URL query parameter. For example `?search=sale`. Typically for `GET` requests.

These fields will normally correspond with pagination and filtering controls on a view.

**"form"**

Included in the request body, as a single item of a JSON object or HTML form. For example `{"colour": "blue", ...}`. Typically for `POST`, `PUT` and `PATCH` requests. Multiple `"form"` fields may be included on a single link.

These fields will normally correspond with serializer fields on a view.

**"body"**

Included as the complete request body. Typically for `POST`, `PUT` and `PATCH` requests. No more than one `"body"` field may exist on a link. May not be used together with `"form"` fields.

These fields will normally correspond with views that use `ListSerializer` to validate the request input, or with file upload views.

#### `encoding`

**"application/json"**

JSON encoded request content. Corresponds to views using `JSONParser`.
Valid only if either one or more `location="form"` fields, or a single
`location="body"` field is included on the `Link`.

**"multipart/form-data"**

Multipart encoded request content. Corresponds to views using `MultiPartParser`.
Valid only if one or more `location="form"` fields is included on the `Link`.

**"application/x-www-form-urlencoded"**

URL encoded request content. Corresponds to views using `FormParser`. Valid
only if one or more `location="form"` fields is included on the `Link`.

**"application/octet-stream"**

Binary upload request content. Corresponds to views using `FileUploadParser`.
Valid only if a `location="body"` field is included on the `Link`.

#### `description`

A short description of the meaning and intended usage of the input field.


---

# Third party packages

## DRF OpenAPI

[DRF OpenAPI][drf-openapi] renders the schema generated by Django Rest Framework
in [OpenAPI][open-api] format.


[cite]: https://blog.heroku.com/archives/2014/1/8/json_schema_for_heroku_platform_api
[coreapi]: http://www.coreapi.org/
[corejson]: http://www.coreapi.org/specification/encoding/#core-json-encoding
[open-api]: https://openapis.org/
[drf-openapi]: https://github.com/limdauto/drf_openapi
[json-hyperschema]: http://json-schema.org/latest/json-schema-hypermedia.html
[api-blueprint]: https://apiblueprint.org/
[static-files]: https://docs.djangoproject.com/en/stable/howto/static-files/
[named-arguments]: https://docs.djangoproject.com/en/stable/topics/http/urls/#named-groups
