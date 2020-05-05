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
            url(r'^api/', include('myproject.api.urls')),
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

## Customizing Schema Generation

You may customize schema generation at the level of the schema as a whole, or
on a per-view basis.

### Schema Level Customization

In order to customize the top-level schema subclass
`rest_framework.schemas.openapi.SchemaGenerator` and provide it as an argument
to the `generateschema` command or `get_schema_view()` helper function.

#### SchemaGenerator

A class that walks a list of routed URL patterns, requests the schema for each
view and collates the resulting OpenAPI schema.

Typically you'll instantiate `SchemaGenerator` with a `title` argument, like so:

    generator = SchemaGenerator(title='Stock Prices API')

Arguments:

* `title` **required**: The name of the API.
* `description`: Longer descriptive text.
* `version`: The version of the API. Defaults to `0.1.0`.
* `url`: The root URL of the API schema. This option is not required unless the schema is included under path prefix.
* `patterns`: A list of URLs to inspect when generating the schema. Defaults to the project's URL conf.
* `urlconf`: A URL conf module name to use when generating the schema. Defaults to `settings.ROOT_URLCONF`.

##### get_schema(self, request)

Returns a dictionary that represents the OpenAPI schema:

    generator = SchemaGenerator(title='Stock Prices API')
    schema = generator.get_schema()

The `request` argument is optional, and may be used if you want to apply
per-user permissions to the resulting schema generation.

This is a good point to override if you want to customize the generated
dictionary,  for example to add custom
[specification extensions][openapi-specification-extensions].

### Per-View Customization

By default, view introspection is performed by an `AutoSchema` instance
accessible via the `schema` attribute on `APIView`. This provides the
appropriate [Open API operation object][openapi-operation] for the view,
request method and path:

    auto_schema = view.schema
    operation = auto_schema.get_operation(...)

In compiling the schema, `SchemaGenerator` calls `view.schema.get_operation()`
for each view, allowed method, and path.

---

**Note**: For basic `APIView` subclasses, default introspection is essentially
limited to the URL kwarg path parameters. For `GenericAPIView`
subclasses, which includes all the provided class based views, `AutoSchema` will
attempt to introspect serializer, pagination and filter fields, as well as
provide richer path field descriptions. (The key hooks here are the relevant
`GenericAPIView` attributes and methods: `get_serializer`, `pagination_class`,
`filter_backends` and so on.)

---

In order to customize the operation generation, you should provide an `AutoSchema` subclass, overriding `get_operation()` as you need:

        from rest_framework.views import APIView
        from rest_framework.schemas.openapi import AutoSchema

        class CustomSchema(AutoSchema):
            def get_operation(...):
                # Implement custom introspection here (or in other sub-methods)

        class CustomView(APIView):
            """APIView subclass with custom schema introspection."""
            schema = CustomSchema()

This provides complete control over view introspection.

You may disable schema generation for a view by setting `schema` to `None`:

    class CustomView(APIView):
        ...
        schema = None  # Will not appear in schema

This also applies to extra actions for `ViewSet`s:

    class CustomViewSet(viewsets.ModelViewSet):

        @action(detail=True, schema=None)
        def extra_action(self, request, pk=None):
            ...

If you wish to provide a base `AutoSchema` subclass to be used throughout your
project you may adjust `settings.DEFAULT_SCHEMA_CLASS`  appropriately.


### Grouping Operations With Tags

Tags can be used to group logical operations. Each tag name in the list MUST be unique. 

---
#### Django REST Framework generates tags automatically with the following logic:

Tag name will be first element from the path. Also, any `_` in path name will be replaced by a `-`.
Consider below examples.

Example 1: Consider a user management system. The following table will illustrate the tag generation logic.
Here first element from the paths is: `users`. Hence tag wil be `users`

Http Method                          |        Path       |     Tags
-------------------------------------|-------------------|-------------
PUT, PATCH, GET(Retrieve), DELETE    |     /users/{id}/  |   ['users']
POST, GET(List)                      |     /users/       |   ['users']

Example 2: Consider a restaurant management system. The System has restaurants. Each restaurant has branches.
Consider REST APIs to deal with a branch of a particular restaurant.
Here first element from the paths is: `restaurants`. Hence tag wil be `restaurants`.

Http Method                          |                         Path                       |     Tags
-------------------------------------|----------------------------------------------------|-------------------
PUT, PATCH, GET(Retrieve), DELETE:   | /restaurants/{restaurant_id}/branches/{branch_id}  |   ['restaurants']
POST, GET(List):                     | /restaurants/{restaurant_id}/branches/             |   ['restaurants']

Example 3: Consider Order items for an e commerce company.

Http Method                          |          Path           |     Tags
-------------------------------------|-------------------------|-------------
PUT, PATCH, GET(Retrieve), DELETE    |     /order_items/{id}/  |   ['order-items']
POST, GET(List)                      |     /order_items/       |   ['order-items']
   

---
#### Overriding auto generated tags:
You can override auto-generated tags by passing `tags` argument to the constructor of `AutoSchema`. `tags` argument must be a list or tuple of string.
```python
from rest_framework.schemas.openapi import AutoSchema
from rest_framework.views import APIView

class MyView(APIView):
    schema = AutoSchema(tags=['tag1', 'tag2'])
    ...
```

If you need more customization, you can override the `get_tags` method of `AutoSchema` class. Consider the following example:

```python
from rest_framework.schemas.openapi import AutoSchema
from rest_framework.views import APIView

class MySchema(AutoSchema):
    ...
    def get_tags(self, path, method):
        if method == 'POST':
            tags = ['tag1', 'tag2']
        elif method == 'GET':
            tags = ['tag2', 'tag3'] 
        elif path == '/example/path/':
            tags = ['tag3', 'tag4']
        else:
            tags = ['tag5', 'tag6', 'tag7']
    
        return tags

class MyView(APIView):
    schema = MySchema()
    ...
```

### OperationId

The schema generator generates an [operationid][openapi-operationid] for each operation. This `operationId` is deduced from the model name, serializer name or view name. The operationId may looks like "listItems", "retrieveItem", "updateItem", etc..
The `operationId` is camelCase by convention.

If you have several views with the same model, the generator may generate duplicate operationId.
In order to work around this, you can override the second part of the operationId: operation name.

```python
from rest_framework.schemas.openapi import AutoSchema

class ExampleView(APIView):
    """APIView subclass with custom schema introspection."""
    schema = AutoSchema(operation_id_base="Custom")
```

The previous example will generate the following operationId: "listCustoms", "retrieveCustom", "updateCustom", "partialUpdateCustom", "destroyCustom".
You need to provide the singular form of he operation name. For the list operation, a "s" will be appended at the end of the operation.

If you need more configuration over the `operationId` field, you can override the `get_operation_id_base` and `get_operation_id` methods from the `AutoSchema` class:

```python
class CustomSchema(AutoSchema):
    def get_operation_id_base(self, path, method, action):
        pass

    def get_operation_id(self, path, method):
        pass

class MyView(APIView):
   schema = AutoSchema(component_name="Ulysses")
```

### Components

Since DRF 3.12, Schema uses the [OpenAPI Components][openapi-components]. This method defines components in the schema and [references them][openapi-reference] inside request and response objects. By default, the component's name is deduced from the Serializer's name.

Using OpenAPI's components provides the following advantages:

* The schema is more readable and lightweight.
* If you use the schema to generate an SDK (using [openapi-generator][openapi-generator] or [swagger-codegen][swagger-codegen]). The generator can name your SDK's models.

### Handling component's schema errors

You may get the following error while generating the schema:
```
"Serializer" is an invalid class name for schema generation.
Serializer's class name should be unique and explicit. e.g. "ItemSerializer".
```

This error occurs when the Serializer name is "Serializer". You should choose a component's name unique across your schema and different than "Serializer".

You may also get the following warning:
```
Schema component "ComponentName" has been overriden with a different value.
```

This warning occurs when different components have the same name in one schema. Your component name should be unique across your project. This is likely an error that may lead to an invalid schema.

You have two ways to solve the previous issues:

* You can rename your serializer with a unique name and another name than "Serializer".
* You can set the `component_name` kwarg parameter of the AutoSchema constructor (see below).
* You can override the `get_component_name` method of the AutoSchema class (see below).

#### Set a custom component's name for your view

To override the component's name in your view, you can use the `component_name` parameter of the AutoSchema constructor:

```python
from rest_framework.schemas.openapi import AutoSchema

class MyView(APIView):
   schema = AutoSchema(component_name="Ulysses")
```

#### Override the default implementation

If you want to have more control and customization about how the schema's components are generated, you can override the `get_component_name` and `get_components` method from the AutoSchema class.

```python
from rest_framework.schemas.openapi import AutoSchema

class CustomSchema(AutoSchema):
	def get_components(self, path, method):
		# Implement your custom implementation

	def get_component_name(self, serializer):
		# Implement your custom implementation

class CustomView(APIView):
    """APIView subclass with custom schema introspection."""
    schema = CustomSchema()
```

[openapi]: https://github.com/OAI/OpenAPI-Specification
[openapi-specification-extensions]: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#specification-extensions
[openapi-operation]: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#operationObject
[openapi-tags]: https://swagger.io/specification/#tagObject
[openapi-operationid]: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#fixed-fields-17
[openapi-components]: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#componentsObject
[openapi-reference]: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#referenceObject
[openapi-generator]: https://github.com/OpenAPITools/openapi-generator
[swagger-codegen]: https://github.com/swagger-api/swagger-codegen
