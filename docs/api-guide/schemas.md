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

### Install `pyyaml`

You'll need to install `pyyaml`, so that you can render your generated schema
into the commonly used YAML-based OpenAPI format.

    pip install pyyaml

### Generating a static schema with the `generateschema` management command

If your schema is static, you can use the `generateschema` management command:

```bash
./manage.py generateschema > openapi-schema.yml
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

In order to customize the top-level schema sublass
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
**Django REST Framework generates tags automatically with following logic:**
1. Extract tag from `ViewSet`. 
    1. If `ViewSet` name ends with `ViewSet`, or `View`; remove it.
    2. Convert class name into lowercase words & join each word with a space. 
    
    Examples:
    
        ViewSet Class   |   Tags
        ----------------|------------
        User            |   ['user']	 
        UserView        |   ['user']	 
        UserViewSet     |   ['user']	
        PascalCaseXYZ   |   ['pascal case xyz']
        IPAddressView   |   ['ip address']

2. If View is not an instance of ViewSet, tag name will be first element from the path. Also, any `-` or `_` in path name will be converted as a space.
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
    PUT, PATCH, GET(Retrieve), DELETE    |     /order-items/{id}/  |   ['order items']
    POST, GET(List)                      |     /order-items/       |   ['order items']
   

---
**You can override auto-generated tags by passing `tags` argument to the constructor of `AutoSchema`.**

**`tags` argument can be a**
1. list of string.
    ```python
   class MyView(APIView):
        ...
        schema = AutoSchema(tags=['tag1', 'tag2'])
   ```
2.  list of dict. This adds metadata to a single tag. Each dict can have 3 possible keys:

    Field name   | Data type | Required | Description 
    -------------|-----------|----------|-------------------------------------------------------------------------
    name         |  string   |   yes    | The name of the tag.
    description  |  string   |    no    | A short description for the tag. [CommonMark syntax](https://spec.commonmark.org/) MAY be used for rich text representation.
    externalDocs |  dict     |    no    | Additional external documentation for this tag. [Click here](https://swagger.io/specification/#externalDocumentationObject) to know more.

    Note: A tag dict with only `name` as a key is logically equivalent to passing a `string` as a tag.

    ```python
    class MyView(APIView):
        ...
        schema = AutoSchema(tags=[
            {
                "name": "user"
            },
            {
                "name": "pet",
                "description": "Everything about your Pets"
            },
            {
                "name": "store",
                "description": "Access to Petstore orders",
                "externalDocs": {
                    "url": "https://example.com",
                    "description": "Find more info here"
                }
            },
        ])
    ```
3. list which is mix of dicts and strings.
    ```python
    class MyView(APIView):
        ...
        schema = AutoSchema(tags=[
            'user',
            {
                "name": "order",
                "description": "Everything about your Pets"
            },
           'pet'
        ])
    ```

[openapi]: https://github.com/OAI/OpenAPI-Specification
[openapi-specification-extensions]: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#specification-extensions
[openapi-operation]: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#operationObject
