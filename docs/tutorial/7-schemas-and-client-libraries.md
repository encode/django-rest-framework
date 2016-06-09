# Tutorial 7: Schemas & Client Libraries

An API schema is a document that describes the available endpoints that
a service provides. Schemas are a useful tool for documentation, and can also
be used to provide information to client libraries, allowing for simpler and
more robust interaction with an API.

## Adding a schema

REST framework supports either explicitly defined schema views, or
automatically generated schemas. Since we're using viewsets and routers,
we can simply use the automatic schema generation.

To include a schema for our API, we add a `schema_title` argument to the
router instantiation.

    router = DefaultRouter(schema_title='Pastebin API')

If you visit the root of the API in a browser you should now see ... TODO

## Using a command line client

Now that our API is exposing a schema endpoint, we can use a dynamic client
library to interact with the API. To demonstrate this, let's install the
Core API command line client.

    $ pip install coreapi-cli

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

TODO - authentication

    $ coreapi action snippets create --param code "print('hello, world')"

    $ coreapi credentials add 127.0.0.1 <username>:<password> --auth basic

## Using a client library

TODO

## Customizing schema generation

TODO
