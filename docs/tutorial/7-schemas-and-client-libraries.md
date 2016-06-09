# Tutorial 7: Schemas & client libraries

A schema is a machine-readable document that describes the available API
endpoints, their URLS, and what operations they support.

Schemas can be a useful tool for auto-generated documentation, and can also
be used to drive dynamic client libraries that can interact with the API.

## Core API

In order to provide schema support REST framework uses [Core API][coreapi].

Core API is a document specification for describing APIs. It is used to provide
an internal representation format of the available endpoints and possible
interactions that an API exposes. It can either be used server-side, or
client-side.

When used server-side, Core API allows an API to support rendering to a wide
range of schema or hypermedia formats.

When used client-side, Core API allows for dynamically driven client libraries
that can interact with any API that exposes a supported schema or hypermedia
format.

## Adding a schema

REST framework supports either explicitly defined schema views, or
automatically generated schemas. Since we're using viewsets and routers,
we can simply use the automatic schema generation.

You'll need to install the `coreapi` python package in order to include an
API schema.

    $ pip install coreapi

We can now include a schema for our API, by adding a `schema_title` argument to
the router instantiation.

    router = DefaultRouter(schema_title='Pastebin API')

If you visit the API root endpoint in a browser you should now see `corejson`
representation become available as an option.

![Schema format](../img/corejson-format.png)

We can also request the schema from the command line, by specifying the desired
content type in the `Accept` header.

    $ http http://127.0.0.1:8000/ Accept:application/vnd.coreapi+json
    HTTP/1.0 200 OK
    Allow: GET, HEAD, OPTIONS
    Content-Type: application/vnd.coreapi+json

    {
        "_meta": {
            "title": "Pastebin API"
        },
        "_type": "document",
        ...

## Using a command line client

Now that our API is exposing a schema endpoint, we can use a dynamic client
library to interact with the API. To demonstrate this, let's use the
Core API command line client. We've already installed the `coreapi` package
using `pip`, so the client tool should already be available. Check that it
is available on the command line...

    $ coreapi
    Usage: coreapi [OPTIONS] COMMAND [ARGS]...

      Command line client for interacting with CoreAPI services.

      Visit http://www.coreapi.org for more information.

    Options:
      --version  Display the package version number.
      --help     Show this message and exit.

    Commands:
    ...

First we'll load the API schema using the command line client.

    $ coreapi get http://127.0.0.1:8000/
    <Pastebin API "http://127.0.0.1:8000/">
        snippets: {
            create(code, [title], [linenos], [language], [style])
            destroy(id)
            highlight(id)
            list()
            partial_update(id, [title], [code], [linenos], [language], [style])
            retrieve(id)
            update(id, code, [title], [linenos], [language], [style])
        }
        users: {
            list()
            retrieve(id)
        }

At this point we're able to see all the available API endpoints.

We can now interact with the API using the command line client:

    $ coreapi action list_snippets

## Authenticating our client

TODO - authentication

    $ coreapi action snippets create --param code "print('hello, world')"

    $ coreapi credentials add 127.0.0.1 <username>:<password> --auth basic

## Using a client library

*TODO - document using python client library, rather than the command line tool.*

## Using another schema format

*TODO - document using OpenAPI instead.*

## Customizing schema generation

*TODO - document writing an explict schema view.*

[coreapi]: http://www.coreapi.org
