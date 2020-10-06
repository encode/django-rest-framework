# Documenting your API

> A REST API should spend almost all of its descriptive effort in defining the media type(s) used for representing resources and driving application state.
>
> &mdash; Roy Fielding, [REST APIs must be hypertext driven][cite]

REST framework provides built-in support for generating OpenAPI schemas, which
can be used with tools that allow you to build API documentation.

There are also a number of great third-party documentation packages available.

## Generating documentation from OpenAPI schemas

There are a number of packages available that allow you to generate HTML
documentation pages from OpenAPI schemas.

Two popular options are [Swagger UI][swagger-ui] and [ReDoc][redoc].

Both require little more than the location of your static schema file or
dynamic `SchemaView` endpoint.

### A minimal example with Swagger UI

Assuming you've followed the example from the schemas documentation for routing
a dynamic `SchemaView`, a minimal Django template for using Swagger UI might be
this:

```html
<!DOCTYPE html>
<html>
  <head>
    <title>Swagger</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" type="text/css" href="//unpkg.com/swagger-ui-dist@3/swagger-ui.css" />
  </head>
  <body>
    <div id="swagger-ui"></div>
    <script src="//unpkg.com/swagger-ui-dist@3/swagger-ui-bundle.js"></script>
    <script>
    const ui = SwaggerUIBundle({
        url: "{% url schema_url %}",
        dom_id: '#swagger-ui',
        presets: [
          SwaggerUIBundle.presets.apis,
          SwaggerUIBundle.SwaggerUIStandalonePreset
        ],
        layout: "BaseLayout",
        requestInterceptor: (request) => {
          request.headers['X-CSRFToken'] = "{{ csrf_token }}"
          return request;
        }
      })
    </script>
  </body>
</html>
```

Save this in your templates folder as `swagger-ui.html`. Then route a
`TemplateView` in your project's URL conf:

```python
from django.views.generic import TemplateView

urlpatterns = [
    # ...
    # Route TemplateView to serve Swagger UI template.
    #   * Provide `extra_context` with view name of `SchemaView`.
    path('swagger-ui/', TemplateView.as_view(
        template_name='swagger-ui.html',
        extra_context={'schema_url':'openapi-schema'}
    ), name='swagger-ui'),
]
```

See the [Swagger UI documentation][swagger-ui] for advanced usage.

### A minimal example with ReDoc.

Assuming you've followed the example from the schemas documentation for routing
a dynamic `SchemaView`, a minimal Django template for using ReDoc might be
this:

```html
<!DOCTYPE html>
<html>
  <head>
    <title>ReDoc</title>
    <!-- needed for adaptive design -->
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
    <!-- ReDoc doesn't change outer page styles -->
    <style>
      body {
        margin: 0;
        padding: 0;
      }
    </style>
  </head>
  <body>
    <redoc spec-url='{% url schema_url %}'></redoc>
    <script src="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js"> </script>
  </body>
</html>
```

Save this in your templates folder as `redoc.html`. Then route a `TemplateView`
in your project's URL conf:

```python
from django.views.generic import TemplateView

urlpatterns = [
    # ...
    # Route TemplateView to serve the ReDoc template.
    #   * Provide `extra_context` with view name of `SchemaView`.
    path('redoc/', TemplateView.as_view(
        template_name='redoc.html',
        extra_context={'schema_url':'openapi-schema'}
    ), name='redoc'),
]
```

See the [ReDoc documentation][redoc] for advanced usage.

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

#### drf-spectacular - Sane and flexible OpenAPI 3.0 schema generation for Django REST framework

[drf-spectacular][drf-spectacular] is a [OpenAPI 3][open-api] schema generation tool with explicit focus on extensibility,
customizability and client generation. Usage patterns are very similar to [drf-yasg][drf-yasg].

It aims to extract as much schema information as possible, while providing decorators and extensions for easy
customization. There is explicit support for [swagger-codegen][swagger], [SwaggerUI][swagger-ui] and [Redoc][redoc],
i18n, versioning, authentication, polymorphism (dynamic requests and responses), query/path/header parameters,
documentation and more. Several popular plugins for DRF are supported out-of-the-box as well.

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

If the python `Markdown` library is installed, then [markdown syntax][markdown] may be used in the docstring, and will be converted to HTML in the browsable API.  For example:

    class AccountListView(views.APIView):
        """
        Returns a list of all **active** accounts in the system.

        For more details on how accounts are activated please [see here][ref].

        [ref]: http://example.com/activating-accounts
        """

Note that when using viewsets the basic docstring is used for all generated views.  To provide descriptions for each view, such as for the list and retrieve views, use docstring sections as described in [Schemas as documentation: Examples][schemas-examples].

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

[cite]: https://roy.gbiv.com/untangled/2008/rest-apis-must-be-hypertext-driven

[hypermedia-docs]: rest-hypermedia-hateoas.md
[metadata-docs]: ../api-guide/metadata.md
[schemas-examples]: ../api-guide/schemas.md#examples

[image-drf-yasg]: ../img/drf-yasg.png
[image-self-describing-api]: ../img/self-describing.png

[drf-yasg]: https://github.com/axnsan12/drf-yasg/
[drf-spectacular]: https://github.com/tfranzel/drf-spectacular/
[markdown]: https://daringfireball.net/projects/markdown/syntax
[open-api]: https://openapis.org/
[redoc]: https://github.com/Rebilly/ReDoc
[swagger]: https://swagger.io/
[swagger-ui]: https://swagger.io/tools/swagger-ui/
