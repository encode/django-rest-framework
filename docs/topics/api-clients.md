# API Clients

An API client handles the underlying details of how network requests are made
and how responses are decoded. They present the developer with an application
interface to work against, rather than working directly with the network interface.

The API clients documented here are not restricted to APIs built with Django REST framework.
 They can be used with any API that exposes a supported schema format.

For example, [the Heroku platform API][heroku-api] exposes a schema in the JSON
Hyperschema format. As a result, the Core API command line client and Python
client library can be [used to interact with the Heroku API][heroku-example].

## Client-side Core API

[Core API][core-api] is a document specification that can be used to describe APIs. It can
be used either server-side, as is done with REST framework's [schema generation][schema-generation],
or used client-side, as described here.

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

To install the Core API command line client, use `pip`.

Note that the command-line client is a separate package to the
python client library. Make sure to install `coreapi-cli`.

    $ pip install coreapi-cli

To start inspecting and interacting with an API the schema must first be loaded
from the network.

    $ coreapi get http://api.example.org/
    <Pastebin API "http://127.0.0.1:8000/">
    snippets: {
        create(code, [title], [linenos], [language], [style])
        destroy(pk)
        highlight(pk)
        list([page])
        partial_update(pk, [title], [code], [linenos], [language], [style])
        retrieve(pk)
        update(pk, code, [title], [linenos], [language], [style])
    }
    users: {
        list([page])
        retrieve(pk)
    }

This will then load the schema, displaying the resulting `Document`. This
`Document` includes all the available interactions that may be made against the API.

To interact with the API, use the `action` command. This command requires a list
of keys that are used to index into the link.

    $ coreapi action users list
    [
        {
            "url": "http://127.0.0.1:8000/users/2/",
            "id": 2,
            "username": "aziz",
            "snippets": []
        },
        ...
    ]

To inspect the underlying HTTP request and response, use the `--debug` flag.

    $ coreapi action users list --debug
    > GET /users/ HTTP/1.1
    > Accept: application/vnd.coreapi+json, */*
    > Authorization: Basic bWF4Om1heA==
    > Host: 127.0.0.1
    > User-Agent: coreapi
    < 200 OK
    < Allow: GET, HEAD, OPTIONS
    < Content-Type: application/json
    < Date: Thu, 30 Jun 2016 10:51:46 GMT
    < Server: WSGIServer/0.1 Python/2.7.10
    < Vary: Accept, Cookie
    <
    < [{"url":"http://127.0.0.1/users/2/","id":2,"username":"aziz","snippets":[]},{"url":"http://127.0.0.1/users/3/","id":3,"username":"amy","snippets":["http://127.0.0.1/snippets/3/"]},{"url":"http://127.0.0.1/users/4/","id":4,"username":"max","snippets":["http://127.0.0.1/snippets/4/","http://127.0.0.1/snippets/5/","http://127.0.0.1/snippets/6/","http://127.0.0.1/snippets/7/"]},{"url":"http://127.0.0.1/users/5/","id":5,"username":"jose","snippets":[]},{"url":"http://127.0.0.1/users/6/","id":6,"username":"admin","snippets":["http://127.0.0.1/snippets/1/","http://127.0.0.1/snippets/2/"]}]

    [
        ...
    ]

Some actions may include optional or required parameters.

    $ coreapi action users create --param username=example

When using `--param`, the type of the input will be determined automatically.

If you want to be more explicit about the parameter type then use `--data` for
any null, numeric, boolean, list, or object inputs, and use `--string` for string inputs.

    $ coreapi action users edit --string username=tomchristie --data is_admin=true

## Authentication & headers

The `credentials` command is used to manage the request `Authentication:` header.
Any credentials added are always linked to a particular domain, so as to ensure
that credentials are not leaked across differing APIs.

The format for adding a new credential is:

    $ coreapi credentials add <domain> <credentials string>

For instance:

    $ coreapi credentials add api.example.org "Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"

The optional `--auth` flag also allows you to add specific types of authentication,
handling the encoding for you. Currently only `"basic"` is supported as an option here.
For example:

    $ coreapi credentials add api.example.org tomchristie:foobar --auth basic

You can also add specific request headers, using the `headers` command:

    $ coreapi headers add api.example.org x-api-version 2

For more information and a listing of the available subcommands use `coreapi
credentials --help` or `coreapi headers --help`.

## Codecs

By default the command line client only includes support for reading Core JSON
schemas, however it includes a plugin system for installing additional codecs.

    $ pip install openapi-codec jsonhyperschema-codec hal-codec
    $ coreapi codecs show
    Codecs
    corejson        application/vnd.coreapi+json encoding, decoding
    hal             application/hal+json         encoding, decoding
    openapi         application/openapi+json     encoding, decoding
    jsonhyperschema application/schema+json      decoding
    json            application/json             data
    text            text/*                       data

## Utilities

The command line client includes functionality for bookmarking API URLs
under a memorable name. For example, you can add a bookmark for the
existing API, like so...

    $ coreapi bookmarks add accountmanagement

There is also functionality for navigating forward or backward through the
history of which API URLs have been accessed.

    $ coreapi history show
    $ coreapi history back

For more information and a listing of the available subcommands use
`coreapi bookmarks --help` or `coreapi history --help`.

## Other commands

To display the current `Document`:

    $ coreapi show

To reload the current `Document` from the network:

    $ coreapi reload

To load a schema file from disk:

    $ coreapi load my-api-schema.json --format corejson

To dump the current document to console in a given format:

    $ coreapi dump --format openapi

To remove the current document, along with all currently saved history,
credentials, headers and bookmarks:

    $ coreapi clear

---

# Python client library

The `coreapi` Python package allows you to programmatically interact with any
API that exposes a supported schema format.

## Getting started

You'll need to install the `coreapi` package using `pip` before you can get
started.

    $ pip install coreapi

In order to start working with an API, we first need a `Client` instance. The
client holds any configuration around which codecs and transports are supported
when interacting with an API, which allows you to provide for more advanced
kinds of behaviour.

    import coreapi
    client = coreapi.Client()

Once we have a `Client` instance, we can fetch an API schema from the network.

    schema = client.get('https://api.example.org/')

The object returned from this call will be a `Document` instance, which is
a representation of the API schema.

## Authentication

Typically you'll also want to provide some authentication credentials when
instantiating the client.

#### Token authentication

The `TokenAuthentication` class can be used to support REST framework's built-in
`TokenAuthentication`, as well as OAuth and JWT schemes.

    auth = coreapi.auth.TokenAuthentication(
        scheme='JWT',
        token='<token>'
    )
    client = coreapi.Client(auth=auth)

When using TokenAuthentication you'll probably need to implement a login flow
using the CoreAPI client.

A suggested pattern for this would be to initially make an unauthenticated client
request to an "obtain token" endpoint

For example, using the "Django REST framework JWT" package

    client = coreapi.Client()
    schema = client.get('https://api.example.org/')

    action = ['api-token-auth', 'create']
    params = {"username": "example", "password": "secret"}
    result = client.action(schema, action, params)

    auth = coreapi.auth.TokenAuthentication(
        scheme='JWT',
        token=result['token']
    )
    client = coreapi.Client(auth=auth)

#### Basic authentication

The `BasicAuthentication` class can be used to support HTTP Basic Authentication.

    auth = coreapi.auth.BasicAuthentication(
        username='<username>',
        password='<password>'
    )
    client = coreapi.Client(auth=auth)

## Interacting with the API

Now that we have a client and have fetched our schema `Document`, we can now
start to interact with the API:

    users = client.action(schema, ['users', 'list'])

Some endpoints may include named parameters, which might be either optional or required:

    new_user = client.action(schema, ['users', 'create'], params={"username": "max"})

## Codecs

Codecs are responsible for encoding or decoding Documents.

The decoding process is used by a client to take a bytestring of an API schema
definition, and returning the Core API `Document` that represents that interface.

A codec should be associated with a particular media type, such as `'application/coreapi+json'`.

This media type is used by the server in the response `Content-Type` header,
in order to indicate what kind of data is being returned in the response.

#### Configuring codecs

The codecs that are available can be configured when instantiating a client.
The keyword argument used here is `decoders`, because in the context of a
client the codecs are only for *decoding* responses.

In the following example we'll configure a client to only accept `Core JSON`
and `JSON` responses. This will allow us to receive and decode a Core JSON schema,
and subsequently to receive JSON responses made against the API.

    from coreapi import codecs, Client

    decoders = [codecs.CoreJSONCodec(), codecs.JSONCodec()]
    client = Client(decoders=decoders)

#### Loading and saving schemas

You can use a codec directly, in order to load an existing schema definition,
and return the resulting `Document`.

    input_file = open('my-api-schema.json', 'rb')
    schema_definition = input_file.read()
    codec = codecs.CoreJSONCodec()
    schema = codec.load(schema_definition)

You can also use a codec directly to generate a schema definition given a `Document` instance:

    schema_definition = codec.dump(schema)
    output_file = open('my-api-schema.json', 'rb')
    output_file.write(schema_definition)

## Transports

Transports are responsible for making network requests. The set of transports
that a client has installed determines which network protocols it is able to
support.

Currently the `coreapi` library only includes an HTTP/HTTPS transport, but
other protocols can also be supported.

#### Configuring transports

The behavior of the network layer can be customized by configuring the
transports that the client is instantiated with.

    import requests
    from coreapi import transports, Client

    credentials = {'api.example.org': 'Token 3bd44a009d16ff'}
    transports = transports.HTTPTransport(credentials=credentials)
    client = Client(transports=transports)

More complex customizations can also be achieved, for example modifying the
underlying `requests.Session` instance to [attach transport adaptors][transport-adaptors]
that modify the outgoing requests.

---

# JavaScript Client Library

The JavaScript client library allows you to interact with your API either from a browser, or using node.

## Installing the JavaScript client

There are two separate JavaScript resources that you need to include in your HTML pages in order to use the JavaScript client library. These are a static `coreapi.js` file, which contains the code for the dynamic client library, and a templated `schema.js` resource, which exposes your API schema.

First, install the API documentation views. These will include the schema resource that'll allow you to load the schema directly from an HTML page, without having to make an asynchronous AJAX call.

    from rest_framework.documentation import include_docs_urls

    urlpatterns = [
        ...
        path('docs/', include_docs_urls(title='My API service'), name='api-docs'),
    ]

Once the API documentation URLs are installed, you'll be able to include both the required JavaScript resources. Note that the ordering of these two lines is important, as the schema loading requires CoreAPI to already be installed.

    <!--
        Load the CoreAPI library and the API schema.

        /static/rest_framework/js/coreapi-0.1.1.js
        /docs/schema.js
    -->
    {% load static %}
    <script src="{% static 'rest_framework/js/coreapi-0.1.1.js' %}"></script>
    <script src="{% url 'api-docs:schema-js' %}"></script>

The `coreapi` library, and the `schema` object will now both be available on the `window` instance.

    const coreapi = window.coreapi;
    const schema = window.schema;

## Instantiating a client

In order to interact with the API you'll need a client instance.

    var client = new coreapi.Client();

Typically you'll also want to provide some authentication credentials when
instantiating the client.

#### Session authentication

The `SessionAuthentication` class allows session cookies to provide the user
authentication. You'll want to provide a standard HTML login flow, to allow
the user to login, and then instantiate a client using session authentication:

    let auth = new coreapi.auth.SessionAuthentication({
        csrfCookieName: 'csrftoken',
        csrfHeaderName: 'X-CSRFToken',
    });
    let client = new coreapi.Client({auth: auth});

The authentication scheme will handle including a CSRF header in any outgoing
requests for unsafe HTTP methods.

#### Token authentication

The `TokenAuthentication` class can be used to support REST framework's built-in
`TokenAuthentication`, as well as OAuth and JWT schemes.

    let auth = new coreapi.auth.TokenAuthentication({
        scheme: 'JWT',
        token: '<token>',
    });
    let client = new coreapi.Client({auth: auth});

When using TokenAuthentication you'll probably need to implement a login flow
using the CoreAPI client.

A suggested pattern for this would be to initially make an unauthenticated client
request to an "obtain token" endpoint

For example, using the "Django REST framework JWT" package

    // Setup some globally accessible state
    window.client = new coreapi.Client();
    window.loggedIn = false;

    function loginUser(username, password) {
        let action = ["api-token-auth", "obtain-token"];
        let params = {username: "example", email: "example@example.com"};
        client.action(schema, action, params).then(function(result) {
            // On success, instantiate an authenticated client.
            let auth = window.coreapi.auth.TokenAuthentication({
                scheme: 'JWT',
                token: result['token'],
            })
            window.client = coreapi.Client({auth: auth});
            window.loggedIn = true;
        }).catch(function (error) {
            // Handle error case where eg. user provides incorrect credentials.
        })
    }

#### Basic authentication

The `BasicAuthentication` class can be used to support HTTP Basic Authentication.

    let auth = new coreapi.auth.BasicAuthentication({
        username: '<username>',
        password: '<password>',
    })
    let client = new coreapi.Client({auth: auth});

## Using the client

Making requests:

    let action = ["users", "list"];
    client.action(schema, action).then(function(result) {
        // Return value is in 'result'
    })

Including parameters:

    let action = ["users", "create"];
    let params = {username: "example", email: "example@example.com"};
    client.action(schema, action, params).then(function(result) {
        // Return value is in 'result'
    })

Handling errors:

    client.action(schema, action, params).then(function(result) {
        // Return value is in 'result'
    }).catch(function (error) {
        // Error value is in 'error'
    })

## Installation with node

The coreapi package is available on NPM.

    $ npm install coreapi
    $ node
    const coreapi = require('coreapi')

You'll either want to include the API schema in your codebase directly, by copying it from the `schema.js` resource, or else load the schema asynchronously. For example:

    let client = new coreapi.Client();
    let schema = null;
    client.get("https://api.example.org/").then(function(data) {
        // Load a CoreJSON API schema.
        schema = data;
        console.log('schema loaded');
    })

[heroku-api]: https://devcenter.heroku.com/categories/platform-api
[heroku-example]: https://www.coreapi.org/tools-and-resources/example-services/#heroku-json-hyper-schema
[core-api]: https://www.coreapi.org/
[schema-generation]: ../api-guide/schemas.md
[transport-adaptors]: http://docs.python-requests.org/en/master/user/advanced/#transport-adapters
