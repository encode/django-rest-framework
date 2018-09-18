# Documenting your API

> A REST API should spend almost all of its descriptive effort in defining the media type(s) used for representing resources and driving application state.
>
> &mdash; Roy Fielding, [REST APIs must be hypertext driven][cite]

REST framework provides built-in support for API documentation. There are also a number of great third-party documentation tools available.

## Built-in API documentation

The built-in API documentation includes:

* Documentation of API endpoints.
* Automatically generated code samples for each of the available API client libraries.
* Support for API interaction.

### Installation

The `coreapi` library is required as a dependency for the API docs. Make sure
to install the latest version. The `pygments` and `markdown` libraries
are optional but recommended.

To install the API documentation, you'll need to include it in your project's URLconf:

    from rest_framework.documentation import include_docs_urls

    urlpatterns = [
        ...
        url(r'^docs/', include_docs_urls(title='My API title'))
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
        url(r'^docs/', include_docs_urls(title='My API title', public=False))
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

## Third party packages

There are a number of mature third-party packages for providing API documentation.

#### drf-yasg - Yet Another Swagger Generator

[drf-yasg][drf-yasg] is a [Swagger][swagger] generation tool implemented without using the schema generation provided
by Django Rest Framework.

It aims to implement as much of the [OpenAPI][open-api] specification as possible - nested schemas, named models,
response bodies, enum/pattern/min/max validators, form parameters, etc. - and to generate documents usable with code
generation tools like `swagger-codegen`.

This also translates into a very useful interactive documentation viewer in the form of `swagger-ui`:


![Screenshot - drf-yasg][image-drf-yasg]


#### DRF OpenAPI

[DRF OpenAPI][drf-openapi] bridges the gap between OpenAPI specification and tool chain with the schema exposed
out-of-the-box by Django Rest Framework. Its goals are:

  * To be dropped into any existing DRF project without any code change necessary.
  * Provide clear disctinction between request schema and response schema.
  * Provide a versioning mechanism for each schema. Support defining schema by version range syntax, e.g. >1.0, <=2.0
  * Support multiple response codes, not just 200
  * All this information should be bound to view methods, not view classes.

It also tries to stay current with the maturing schema generation mechanism provided by DRF.

![Screenshot - DRF OpenAPI][image-drf-openapi]

---

#### DRF Docs

[DRF Docs][drfdocs-repo] allows you to document Web APIs made with Django REST Framework and it is authored by Emmanouil Konstantinidis. It's made to work out of the box and its setup should not take more than a couple of minutes. Complete documentation can be found on the [website][drfdocs-website] while there is also a [demo][drfdocs-demo] available for people to see what it looks like. **Live API Endpoints** allow you to utilize the endpoints from within the documentation in a neat way.

Features include customizing the template with your branding, settings for hiding the docs depending on the environment and more.

Both this package and Django REST Swagger are fully documented, well supported, and come highly recommended.

![Screenshot - DRF docs][image-drf-docs]

---

#### Django REST Swagger

Marc Gibbons' [Django REST Swagger][django-rest-swagger] integrates REST framework with the [Swagger][swagger] API documentation tool.  The package produces well presented API documentation, and includes interactive tools for testing API endpoints.

Django REST Swagger supports REST framework versions 2.3 and above.

Mark is also the author of the [REST Framework Docs][rest-framework-docs] package which offers clean, simple autogenerated documentation for your API but is deprecated and has moved to Django REST Swagger.

Both this package and DRF docs are fully documented, well supported, and come highly recommended.

![Screenshot - Django REST Swagger][image-django-rest-swagger]

---

### DRF AutoDocs

Oleksander Mashianovs' [DRF Auto Docs][drfautodocs-repo] automated api renderer.

Collects almost all the code you written into documentation effortlessly.

Supports:

 * functional view docs
 * tree-like structure
 * Docstrings:
  * markdown
  * preserve space & newlines
  * formatting with nice syntax
 * Fields:
  * choices rendering
  * help_text (to specify SerializerMethodField output, etc)
  * smart read_only/required rendering
 * Endpoint properties:
  * filter_backends
  * authentication_classes
  * permission_classes
  * extra url params(GET params)

![whole structure](http://joxi.ru/52aBGNI4k3oyA0.jpg)

---

#### Apiary

There are various other online tools and services for providing API documentation.  One notable service is [Apiary][apiary].  With Apiary, you describe your API using a simple markdown-like syntax.  The generated documentation includes API interaction, a mock server for testing & prototyping, and various other tools.

![Screenshot - Apiary][image-apiary]

---

## Self describing APIs

The browsable API that REST framework provides makes it possible for your API to be entirely self describing.  The documentation for each API endpoint can be provided simply by visiting the URL in your browser.

![Screenshot - Self describing API][image-self-describing-api]

---

#### Setting the title

The title that is used in the browsable API is generated from the view class name or function name.  Any trailing `View` or `ViewSet` suffix is stripped, and the string is whitespace separated on uppercase/lowercase boundaries or underscores.

For example, the view `UserListView`, will be named `User List` when presented in the browsable API.

When working with viewsets, an appropriate suffix is appended to each generated view.  For example, the view set `UserViewSet` will generate views named `User List` and `User Instance`.

#### Setting the description

The description in the browsable API is generated from the docstring of the view or viewset.

If the python `markdown` library is installed, then [markdown syntax][markdown] may be used in the docstring, and will be converted to HTML in the browsable API.  For example:

    class AccountListView(views.APIView):
        """
        Returns a list of all **active** accounts in the system.

        For more details on how accounts are activated please [see here][ref].

        [ref]: http://example.com/activating-accounts
        """

Note that when using viewsets the basic docstring is used for all generated views.  To provide descriptions for each view, such as for the the list and retrieve views, use docstring sections as described in [Schemas as documentation: Examples][schemas-examples].

#### The `OPTIONS` method

REST framework APIs also support programmatically accessible descriptions, using the `OPTIONS` HTTP method.  A view will respond to an `OPTIONS` request with metadata including the name, description, and the various media types it accepts and responds with.

When using the generic views, any `OPTIONS` requests will additionally respond with metadata regarding any `POST` or `PUT` actions available, describing which fields are on the serializer.

You can modify the response behavior to `OPTIONS` requests by overriding the `options` view method and/or by providing a custom Metadata class.  For example:

    def options(self, request, *args, **kwargs):
        """
        Don't include the view description in OPTIONS responses.
        """
        meta = self.metadata_class()
        data = meta.determine_metadata(request, self)
        data.pop('description')
        return data

See [the Metadata docs][metadata-docs] for more details.

---

## The hypermedia approach

To be fully RESTful an API should present its available actions as hypermedia controls in the responses that it sends.

In this approach, rather than documenting the available API endpoints up front, the description instead concentrates on the *media types* that are used.  The available actions that may be taken on any given URL are not strictly fixed, but are instead made available by the presence of link and form controls in the returned document.

To implement a hypermedia API you'll need to decide on an appropriate media type for the API, and implement a custom renderer and parser for that media type.  The [REST, Hypermedia & HATEOAS][hypermedia-docs] section of the documentation includes pointers to background reading, as well as links to various hypermedia formats.

[cite]: http://roy.gbiv.com/untangled/2008/rest-apis-must-be-hypertext-driven
[drf-yasg]: https://github.com/axnsan12/drf-yasg/
[image-drf-yasg]: ../img/drf-yasg.png
[drf-openapi]: https://github.com/limdauto/drf_openapi/
[image-drf-openapi]: ../img/drf-openapi.png
[drfdocs-repo]: https://github.com/ekonstantinidis/django-rest-framework-docs
[drfdocs-website]: https://www.drfdocs.com/
[drfdocs-demo]: http://demo.drfdocs.com/
[drfautodocs-repo]: https://github.com/iMakedonsky/drf-autodocs
[django-rest-swagger]: https://github.com/marcgibbons/django-rest-swagger
[swagger]: https://swagger.io/
[open-api]: https://openapis.org/
[rest-framework-docs]: https://github.com/marcgibbons/django-rest-framework-docs
[apiary]: https://apiary.io/
[markdown]: https://daringfireball.net/projects/markdown/
[hypermedia-docs]: rest-hypermedia-hateoas.md
[image-drf-docs]: ../img/drfdocs.png
[image-django-rest-swagger]: ../img/django-rest-swagger.png
[image-apiary]: ../img/apiary.png
[image-self-describing-api]: ../img/self-describing.png
[schemas-examples]: ../api-guide/schemas/#examples
[metadata-docs]: ../api-guide/metadata/
[client-library-templates]: https://github.com/encode/django-rest-framework/tree/master/rest_framework/templates/rest_framework/docs/langs
