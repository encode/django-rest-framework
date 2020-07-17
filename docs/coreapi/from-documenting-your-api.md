
## Built-in API documentation

The built-in API documentation includes:

* Documentation of API endpoints.
* Automatically generated code samples for each of the available API client libraries.
* Support for API interaction.

### Installation

The `coreapi` library is required as a dependency for the API docs. Make sure
to install the latest version. The `Pygments` and `Markdown` libraries
are optional but recommended.

To install the API documentation, you'll need to include it in your project's URLconf:

    from rest_framework.documentation import include_docs_urls

    urlpatterns = [
        ...
        path('docs/', include_docs_urls(title='My API title'))
    ]

This will include two different views:

  * `/docs/` - The documentation page itself.
  * `/docs/schema.js` - A JavaScript resource that exposes the API schema.

---

**Note**: By default `include_docs_urls` configures the underlying `SchemaView` to generate _public_ schemas.
This means that views will not be instantiated with a `request` instance. i.e. Inside the view `self.request` will be `None`.

To be compatible with this behaviour, methods (such as `get_serializer` or `get_serializer_class` etc.) which inspect `self.request` or, particularly, `self.request.user` may need to be adjusted to handle this case.

You may ensure views are given a `request` instance by calling `include_docs_urls` with `public=False`:

    from rest_framework.documentation import include_docs_urls

    urlpatterns = [
        ...
        # Generate schema with valid `request` instance:
        path('docs/', include_docs_urls(title='My API title', public=False))
    ]


---


### Documenting your views

You can document your views by including docstrings that describe each of the available actions.
For example:

    class UserList(generics.ListAPIView):
        """
        Return a list of all the existing users.
        """

If a view supports multiple methods, you should split your documentation using `method:` style delimiters.

    class UserList(generics.ListCreateAPIView):
        """
        get:
        Return a list of all the existing users.

        post:
        Create a new user instance.
        """

When using viewsets, you should use the relevant action names as delimiters.

    class UserViewSet(viewsets.ModelViewSet):
        """
        retrieve:
        Return the given user.

        list:
        Return a list of all the existing users.

        create:
        Create a new user instance.
        """

Custom actions on viewsets can also be documented in a similar way using the method names
as delimiters or by attaching the documentation to action mapping methods.

    class UserViewSet(viewsets.ModelViewset):
        ...

        @action(detail=False, methods=['get', 'post'])
        def some_action(self, request, *args, **kwargs):
            """
            get:
            A description of the get method on the custom action.

            post:
            A description of the post method on the custom action.
            """

        @some_action.mapping.put
        def put_some_action():
            """
            A description of the put method on the custom action.
            """


### `documentation` API Reference

The `rest_framework.documentation` module provides three helper functions to help configure the interactive API documentation, `include_docs_urls` (usage shown above), `get_docs_view` and `get_schemajs_view`.

 `include_docs_urls` employs `get_docs_view` and `get_schemajs_view` to generate the url patterns for the documentation page and JavaScript resource that exposes the API schema respectively. They expose the following options for customisation. (`get_docs_view` and `get_schemajs_view` ultimately call `rest_frameworks.schemas.get_schema_view()`, see the Schemas docs for more options there.)

#### `include_docs_urls`

* `title`: Default `None`. May be used to provide a descriptive title for the schema definition.
* `description`: Default `None`. May be used to provide a description for the schema definition.
* `schema_url`: Default `None`. May be used to pass a canonical base URL for the schema.
* `public`: Default `True`. Should the schema be considered _public_? If `True` schema is generated without a `request` instance being passed to views.
* `patterns`: Default `None`. A list of URLs to inspect when generating the schema. If `None` project's URL conf will be used.
* `generator_class`: Default `rest_framework.schemas.SchemaGenerator`. May be used to specify a `SchemaGenerator` subclass to be passed to the `SchemaView`.
* `authentication_classes`: Default `api_settings.DEFAULT_AUTHENTICATION_CLASSES`. May be used to pass custom authentication classes to the `SchemaView`.
* `permission_classes`: Default `api_settings.DEFAULT_PERMISSION_CLASSES` May be used to pass custom permission classes to the `SchemaView`.
* `renderer_classes`: Default `None`. May be used to pass custom renderer classes to the `SchemaView`.

#### `get_docs_view`

* `title`: Default `None`. May be used to provide a descriptive title for the schema definition.
* `description`: Default `None`. May be used to provide a description for the schema definition.
* `schema_url`: Default `None`. May be used to pass a canonical base URL for the schema.
* `public`: Default `True`. If `True` schema is generated without a `request` instance being passed to views.
* `patterns`: Default `None`. A list of URLs to inspect when generating the schema. If `None` project's URL conf will be used.
* `generator_class`: Default `rest_framework.schemas.SchemaGenerator`. May be used to specify a `SchemaGenerator` subclass to be passed to the `SchemaView`.
* `authentication_classes`: Default `api_settings.DEFAULT_AUTHENTICATION_CLASSES`. May be used to pass custom authentication classes to the `SchemaView`.
* `permission_classes`: Default `api_settings.DEFAULT_PERMISSION_CLASSES`. May be used to pass custom permission classes to the `SchemaView`.
* `renderer_classes`: Default `None`. May be used to pass custom renderer classes to the `SchemaView`. If `None` the `SchemaView` will be configured with `DocumentationRenderer` and `CoreJSONRenderer` renderers, corresponding to the (default) `html` and `corejson` formats.

#### `get_schemajs_view`

* `title`: Default `None`. May be used to provide a descriptive title for the schema definition.
* `description`: Default `None`. May be used to provide a description for the schema definition.
* `schema_url`: Default `None`. May be used to pass a canonical base URL for the schema.
* `public`: Default `True`. If `True` schema is generated without a `request` instance being passed to views.
* `patterns`: Default `None`. A list of URLs to inspect when generating the schema. If `None` project's URL conf will be used.
* `generator_class`: Default `rest_framework.schemas.SchemaGenerator`. May be used to specify a `SchemaGenerator` subclass to be passed to the `SchemaView`.
* `authentication_classes`: Default `api_settings.DEFAULT_AUTHENTICATION_CLASSES`. May be used to pass custom authentication classes to the `SchemaView`.
* `permission_classes`: Default `api_settings.DEFAULT_PERMISSION_CLASSES` May be used to pass custom permission classes to the `SchemaView`.


### Customising code samples

The built-in API documentation includes automatically generated code samples for
each of the available API client libraries.

You may customise these samples by subclassing `DocumentationRenderer`, setting
`languages` to the list of languages you wish to support:

    from rest_framework.renderers import DocumentationRenderer


    class CustomRenderer(DocumentationRenderer):
        languages = ['ruby', 'go']

For each language you need to provide an `intro` template, detailing installation instructions and such,
plus a generic template for making API requests, that can be filled with individual request details.
See the [templates for the bundled languages][client-library-templates] for examples.

---

[client-library-templates]: https://github.com/encode/django-rest-framework/tree/master/rest_framework/templates/rest_framework/docs/langs