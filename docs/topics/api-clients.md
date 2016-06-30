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

To start inspecting and interacting with an API the schema must be loaded.

    coreapi get http://api.example.org/

This will then load the schema, displaying the resulting `Document`. This
`Document` includes all the available interactions that may be made against the API.

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

To display the current `Document`:

    coreapi show

To reload the current `Document` from the network:

    coreapi reload

To load a schema file from disk:

    coreapi load my-api-schema.json --format corejson

To remove the current document, along with all currently saved history,
credentials, headers and bookmarks:

    coreapi clear

---

# Python client library

The `coreapi` Python package allows you to programatically interact with any
API that exposes a supported schema format.

## Getting started

You'll need to install the `coreapi` package using `pip` before you can get
started. Once you've done so, open up a python terminal.

In order to start working with an API, we first need a `Client` instance. The
client holds any configuration around which codecs and transports are supported
when interacting with an API, which allows you to provide for more advanced
kinds of behaviour.

    import coreapi
    client = coreapi.Client()

Once we have a `Client` instance, we can fetch an API schema from the network.

    schema = client.get('https://api.example.org/')

The object returned from this call will be a `Document` instance, which is
the internal representation of the interface that we are interacting with.

Now that we have our schema `Document`, we can now start to interact with the API:

    users = client.action(schema, ['users', 'list'])

Some endpoints may include named parameters, which might be either optional or required:

    new_user = client.action(schema, ['users', 'create'], params={"username": "max"})

**TODO**: *file uploads*, *describe/help?*

## Codecs

Codecs are responsible for encoding or decoding Documents.

The decoding process is used by a client to take a bytestring of an API schema
definition, and returning the Core API `Document` that represents that interface.

A codec should be associated with a particular media type, such as **TODO**.

This media type is used by the server in the response `Content-Type` header,
in order to indicate what kind of data is being returned in the response.

#### Configuring codecs

**TODO**

#### Loading and saving schemas

You can use a codec directly, in order to load an existing schema definition,
and return the resulting `Document`.

    schema_definition = open('my-api-schema.json', 'r').read()
    codec = codecs.CoreJSONCodec()
    schema = codec.load(schema_definition)

You can also use a codec directly to generate a schema definition given a `Document` instance:

    schema_definition = codec.dump(schema)
    output_file = open('my-api-schema.json', 'r')
    output_file.write(schema_definition)

#### Writing custom codecs

## Transports

**TODO**

#### Configuring transports

**TODO**

#### Writing custom transports

**TODO**
