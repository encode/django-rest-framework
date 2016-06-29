# API Clients

An API client handles the underlying details of how network requests are made
and how responses are decoded. They present the developer with an application
interface to work against, rather than working directly with the network interface.

The API clients documented here are not restricted to REST framework APIs,
and *can be used with any API that exposes a supported schema format*.

## Client-side Core API

Core API is a document specification that can be used to describe APIs. It can
be used either server-side, as is done with REST framework's Schema generation,
or used client-side, as described here

When used client-side, Core API allows for *dynamically driven client libraries*
that can interact with any API that exposes a supported schema or hypermedia
format.

Using a dynamically driven client has a number of advantages over interacting
with an API by building HTTP requests directly.

#### More meaningful interaction

API interactions are presented in a more meaningful way. You're working at
the application interface layer, rather than the network interface layer.

#### Resilience & evolvability

The client determines what endpoints are available, what parameters exist
against each particular endpoint, and how HTTP requests are formed.

This also allows for a degree of API evolvability. URLs can be modified
without breaking existing clients, or more efficient encodings can be used
on-the-wire, with clients transparently upgrading.

#### Self-descriptive APIs

A dynamically driven client is able to present documentation on the API to the
end user. This documentation allows the user to discover the available endpoints
and parameters, and better understand the API they are working with.

Because this documentation is driven by the API schema it will always be fully
up to date with the most recently deployed version of the service.

---

# Command line client

The command line client allows you to inspect and interact with any API that
exposes a supported schema format.

## Getting started

To install the Core API command line client, use pip.

    pip install coreapi

**TODO**

    coreapi get http://api.example.org/

To interact with the API, use the `action` command. This command requires a list
of keys that are used to index into the link.

    coreapi action users list

Some actions may include optional or required parameters.

    coreapi action users create --params username example

To inspect the underlying HTTP request and response, use the `--debug` flag.

    coreapi action users create --params username example --debug

To see some brief documentation on a particular link, use the `describe` command,
passing a list of keys that index into the link.

    coreapi describe users create

**TODO**:

* string params / data params
* file uploads
* file downloads

## Authentication & headers

The `credentials` command is used to manage the request `Authentication:` header.
Any credentials added are always linked to a particular domain, so as to ensure
that credentials are not leaked across differing APIs.

The format for adding a new credential is:

    coreapi credentials add <domain> <credentials string>

For instance:

    coreapi credentials add api.example.org "Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"

The optional `--auth` flag also allows you to add specific types of authentication,
handling the encoding for you. Currently only `"basic"` is supported as an option here.
For example:

    coreapi credentials add api.example.org tomchristie:foobar --auth basic

You can also add specific request headers, using the `headers` command:

    coreapi headers add api.example.org x-api-version 2

For more information and a listing of the available subcommands use `coreapi
credentials --help` or `coreapi headers --help`.

## Utilities

The command line client includes functionality for bookmarking API URLs
under a memorable name. For example, you can add a bookmark for the
existing API, like so...

    coreapi bookmarks add accountmanagement

There is also functionality for navigating forward or backward through the
history of which API URLs have been accessed.

    coreapi history show
    coreapi history back

For more information and a listing of the available subcommands use
`coreapi bookmarks --help` or `coreapi history --help`.

## Other commands

**TODO**

To display the current `Document`, use the `show` command.

    coreapi show

To reload the current `Document` from the network, use `reload`.

    coreapi reload

To load a schema file from disk.

    load

To remove the current document, history, credentials, headers and bookmarks, use `clear`:

    coreapi clear

---

# Python client library

The `coreapi` Python package allows you to programatically interact with any
API that exposes a supported schema format.

## Getting started

    client = coreapi.Client()
    schema = client.get('http://...')

    client.action(schema, ['users', 'list'])
    client.action(schema, ['users', 'list'], params={"page": 2})

## Codecs

## Transports
