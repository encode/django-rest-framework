---
source:
    - schemas
---

# Schema

> A machine-readable [schema] describes what resources are available via the API, what their URLs are, how they are represented and what operations they support.
>
> &mdash; Heroku, [JSON Schema for the Heroku Platform API][cite]

API schemas are a useful tool that allow for a range of use cases, including
generating reference documentation, or driving dynamic client libraries that
can interact with your API.

Django REST Framework provides support for automatic generation of
[OpenAPI][openapi] schemas.

## Overview

Schema generation has several moving parts. It's worth having an overview:

* `SchemaGenerator` is a top-level class that is responsible for walking your
  configured URL patterns, finding `APIView` subclasses, enquiring for their
  schema representation, and compiling the final schema object.
* `AutoSchema` encapsulates all the details necessary for per-view schema
  introspection. Is attached to each view via the `schema` attribute. You
  subclass `AutoSchema` in order to customize your schema.
* The `generateschema` management command allows you to generate a static schema
  offline.
* Alternatively, you can route `SchemaView` to dynamically generate and serve
  your schema.
* `settings.DEFAULT_SCHEMA_CLASS` allows you to specify an `AutoSchema`
  subclass to serve as your project's default.

The following sections explain more.

## Generating an OpenAPI Schema

### Install dependencies

    pip install pyyaml uritemplate

* `pyyaml` is used to generate schema into YAML-based OpenAPI format.
* `uritemplate` is used internally to get parameters in path.

### Generating a static schema with the `generateschema` management command

If your schema is static, you can use the `generateschema` management command:

```bash
./manage.py generateschema --file openapi-schema.yml
```

Once you've generated a schema in this way you can annotate it with any
additional information that cannot be automatically inferred by the schema
generator.

You might want to check your API schema into version control and update it
with each new release, or serve the API schema from your site's static media.

### Generating a dynamic schema with `SchemaView`

If you require a dynamic schema, because foreign key choices depend on database
values, for example, you can route a `SchemaView` that will generate and serve
your schema on demand.

To route a `SchemaView`, use the `get_schema_view()` helper.

In `urls.py`:

```python
from rest_framework.schemas import get_schema_view

urlpatterns = [
    # ...
    # Use the `get_schema_view()` helper to add a `SchemaView` to project URLs.
    #   * `title` and `description` parameters are passed to `SchemaGenerator`.
    #   * Provide view name for use with `reverse()`.
    path('openapi', get_schema_view(
        title="Your Project",
        description="API for all things …",
        version="1.0.0"
    ), name='openapi-schema'),
    # ...
]
```

#### `get_schema_view()`

The `get_schema_view()` helper takes the following keyword arguments:

* `title`: May be used to provide a descriptive title for the schema definition.
* `description`: Longer descriptive text.
* `version`: The version of the API.
* `url`: May be used to pass a canonical base URL for the schema.

        schema_view = get_schema_view(
            title='Server Monitoring API',
            url='https://www.example.org/api/'
        )

* `urlconf`: A string representing the import path to the URL conf that you want
   to generate an API schema for. This defaults to the value of Django's
   `ROOT_URLCONF` setting.

        schema_view = get_schema_view(
            title='Server Monitoring API',
            url='https://www.example.org/api/',
            urlconf='myproject.urls'
        )

* `patterns`: List of url patterns to limit the schema introspection to. If you
  only want the `myproject.api` urls to be exposed in the schema:

        schema_url_patterns = [
            path('api/', include('myproject.api.urls')),
        ]

        schema_view = get_schema_view(
            title='Server Monitoring API',
            url='https://www.example.org/api/',
            patterns=schema_url_patterns,
        )

* `generator_class`: May be used to specify a `SchemaGenerator` subclass to be
  passed to the `SchemaView`.
* `authentication_classes`: May be used to specify the list of authentication
  classes that will apply to the schema endpoint. Defaults to
  `settings.DEFAULT_AUTHENTICATION_CLASSES`
* `permission_classes`: May be used to specify the list of permission classes
  that will apply to the schema endpoint. Defaults to
  `settings.DEFAULT_PERMISSION_CLASSES`.
* `renderer_classes`: May be used to pass the set of renderer classes that can
  be used to render the API root endpoint.


## SchemaGenerator

**Schema-level customization**

```python
from rest_framework.schemas.openapi import SchemaGenerator
```

`SchemaGenerator` is a class that walks a list of routed URL patterns, requests
the schema for each view and collates the resulting OpenAPI schema.

Typically you won't need to instantiate `SchemaGenerator` yourself, but you can
do so like so:

    generator = SchemaGenerator(title='Stock Prices API')

Arguments:

* `title` **required**: The name of the API.
* `description`: Longer descriptive text.
* `version`: The version of the API. Defaults to `0.1.0`.
* `url`: The root URL of the API schema. This option is not required unless the schema is included under path prefix.
* `patterns`: A list of URLs to inspect when generating the schema. Defaults to the project's URL conf.
* `urlconf`: A URL conf module name to use when generating the schema. Defaults to `settings.ROOT_URLCONF`.

In order to customize the top-level schema, subclass
`rest_framework.schemas.openapi.SchemaGenerator` and provide your subclass
as an argument to the `generateschema` command or `get_schema_view()` helper
function.

### get_schema(self, request)

Returns a dictionary that represents the OpenAPI schema:

    generator = SchemaGenerator(title='Stock Prices API')
    schema = generator.get_schema()

The `request` argument is optional, and may be used if you want to apply
per-user permissions to the resulting schema generation.

This is a good point to override if you want to customize the generated
dictionary For example you might wish to add terms of service to the [top-level
`info` object][info-object]:

```
class TOSSchemaGenerator(SchemaGenerator):
    def get_schema(self, *args, **kwargs):
        schema = super().get_schema(*args, **kwargs)
        schema["info"]["termsOfService"] = "https://example.com/tos.html"
        return schema
```

## AutoSchema

**Per-View Customization**

```python
from rest_framework.schemas.openapi import AutoSchema
```

By default, view introspection is performed by an `AutoSchema` instance
accessible via the `schema` attribute on `APIView`.

    auto_schema = some_view.schema

`AutoSchema` provides the OpenAPI elements needed for each view, request method
and path:

* A list of [OpenAPI components][openapi-components]. In DRF terms these are
  mappings of serializers that describe request and response bodies.
* The appropriate [OpenAPI operation object][openapi-operation] that describes
  the endpoint, including path and query parameters for pagination, filtering,
  and so on.

```python
components = auto_schema.get_components(...)
operation = auto_schema.get_operation(...)
```

In compiling the schema, `SchemaGenerator` calls `get_components()` and
`get_operation()` for each view, allowed method, and path.

----

**Note**: The automatic introspection of components, and many operation
parameters relies on the relevant attributes and methods of
`GenericAPIView`: `get_serializer()`, `pagination_class`, `filter_backends`,
etc. For basic `APIView` subclasses, default introspection is essentially limited to
the URL kwarg path parameters for this reason.

----

`AutoSchema` encapsulates the view introspection needed for schema generation.
Because of this all the schema generation logic is kept in a single place,
rather than being spread around the already extensive view, serializer and
field APIs.

Keeping with this pattern, try not to let schema logic leak into your own
views, serializers, or fields when customizing the schema generation. You might
be tempted to do something like this:

```python
class CustomSchema(AutoSchema):
    """
    AutoSchema subclass using schema_extra_info on the view.
    """
    ...

class CustomView(APIView):
    schema = CustomSchema()
    schema_extra_info = ... some extra info ...
```

Here, the `AutoSchema` subclass goes looking for `schema_extra_info` on the
view. This is _OK_ (it doesn't actually hurt) but it means you'll end up with
your schema logic spread out in a number of different places.

Instead try to subclass `AutoSchema` such that the `extra_info` doesn't leak
out into the view:

```python
class BaseSchema(AutoSchema):
    """
    AutoSchema subclass that knows how to use extra_info.
    """
    ...

class CustomSchema(BaseSchema):
    extra_info = ... some extra info ...

class CustomView(APIView):
    schema = CustomSchema()
```

This style is slightly more verbose but maintains the encapsulation of the
schema related code. It's more _cohesive_ in the _parlance_. It'll keep the
rest of your API code more tidy.

If an option applies to many view classes, rather than creating a specific
subclass per-view, you may find it more convenient to allow specifying the
option as an `__init__()` kwarg to your base `AutoSchema` subclass:

```python
class CustomSchema(BaseSchema):
    def __init__(self, **kwargs):
        # store extra_info for later
        self.extra_info = kwargs.pop("extra_info")
        super().__init__(**kwargs)

class CustomView(APIView):
    schema = CustomSchema(
        extra_info=... some extra info ...
    )
```

This saves you having to create a custom subclass per-view for a commonly used option.

Not all `AutoSchema` methods expose related  `__init__()` kwargs, but those for
the more commonly needed options do.

### `AutoSchema` methods

#### `get_components()`

Generates the OpenAPI components that describe request and response bodies,
deriving  their properties from the serializer.

Returns a dictionary mapping the component name to the generated
representation. By default this has just a single pair but you may override
`get_components()` to return multiple pairs if your view uses multiple
serializers.

#### `get_component_name()`

Computes the component's name from the serializer.

You may see warnings if your API has duplicate component names. If so you can override `get_component_name()` or pass the `component_name` `__init__()` kwarg (see below) to provide different names.

#### `map_serializer()`

Maps serializers to their OpenAPI representations.

Most serializers should conform to the standard OpenAPI `object` type, but you may
wish to override `map_serializer()` in order to customize this or other
serializer-level fields.

#### `map_field()`

Maps individual serializer fields to their schema representation. The base implementation
will handle the default fields that Django REST Framework provides.

For `SerializerMethodField` instances, for which the schema is unknown, or custom field subclasses you should override `map_field()` to generate the correct schema:

```python
class CustomSchema(AutoSchema):
    """Extension of ``AutoSchema`` to add support for custom field schemas."""

    def map_field(self, field):
        # Handle SerializerMethodFields or custom fields here...
        # ...
        return super().map_field(field)
```

Authors of third-party packages should aim to provide an `AutoSchema` subclass,
and a mixin, overriding `map_field()` so that users can easily generate schemas
for their custom fields.

#### `get_tags()`

OpenAPI groups operations by tags. By default tags taken from the first path
segment of the routed URL. For example, a URL like `/users/{id}/` will generate
the tag `users`.

You can pass an `__init__()` kwarg to manually specify tags (see below), or
override `get_tags()` to provide custom logic.

#### `get_operation()`

Returns the [OpenAPI operation object][openapi-operation] that describes the
endpoint, including path and query parameters for pagination, filtering, and so
on.

Together with `get_components()`, this is the main entry point to the view
introspection.

#### `get_operation_id()`

There must be a unique [operationid](openapi-operationid) for each operation.
By default the `operationId` is deduced from the model name, serializer name or
view name. The operationId looks like "listItems", "retrieveItem",
"updateItem", etc. The `operationId` is camelCase by convention.

#### `get_operation_id_base()`

If you have several views with the same model name, you may see duplicate
operationIds.

In order to work around this, you can override `get_operation_id_base()` to
provide a different base for name part of the ID.

### `AutoSchema.__init__()` kwargs

`AutoSchema` provides a number of `__init__()` kwargs that can be used for
common customizations, if the default generated values are not appropriate.

The available kwargs are:

* `tags`: Specify a list of tags.
* `component_name`: Specify the component name.
* `operation_id_base`: Specify the resource-name part of operation IDs.

You pass the kwargs when declaring the `AutoSchema` instance on your view:

```
class PetDetailView(generics.RetrieveUpdateDestroyAPIView):
    schema = AutoSchema(
        tags=['Pets'],
        component_name='Pet',
        operation_id_base='Pet',
    )
    ...
```

Assuming a `Pet` model and `PetSerializer` serializer, the kwargs in this
example are probably not needed. Often, though, you'll need to pass the kwargs
if you have multiple view targeting the same model, or have multiple views with
identically named serializers.

If your views have related customizations that are needed frequently, you can
create a base `AutoSchema` subclass for your project that takes additional
`__init__()` kwargs to save subclassing `AutoSchema` for each view.

[openapi]: https://github.com/OAI/OpenAPI-Specification
[openapi-specification-extensions]: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#specification-extensions
[openapi-operation]: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#operationObject
[openapi-tags]: https://swagger.io/specification/#tagObject
[openapi-operationid]: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#fixed-fields-17
[openapi-components]: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#componentsObject
[openapi-reference]: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#referenceObject
[openapi-generator]: https://github.com/OpenAPITools/openapi-generator
[swagger-codegen]: https://github.com/swagger-api/swagger-codegen
[info-object]: https://swagger.io/specification/#infoObject
