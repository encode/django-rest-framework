:mod:`resource` 
===============

The :mod:`resource` module is the core of FlyWheel.  It provides the :class:`Resource` base class which handles incoming HTTP requests and maps them to method calls, performing authentication, input deserialization, input validation, output serialization.

Resources are created by sublassing :class:`Resource`, setting a number of class attributes, and overriding one or more methods.

:class:`Resource` class attributes
----------------------------------

The following class attributes determine the behavior of the Resource and are intended to be overridden.

.. attribute:: Resource.allowed_methods

  A list of the HTTP methods that the Resource supports.
  HTTP requests to the resource that do not map to an allowed operation will result in a 405 Method Not Allowed response.

  Default: ``('GET',)``

.. attribute:: Resource.anon_allowed_methods

  A list of the HTTP methods that the Resource supports for unauthenticated users.
  Unauthenticated HTTP requests to the resource that do not map to an allowed operation will result in a 405 Method Not Allowed response.

  Default: ``()``

.. attribute:: Resource.emitters

  Lists the set of emitters that the Resource supports.  This determines which media types the resource can serialize it's output to.  Clients can specify which media types they accept using standard HTTP content negotiation via the Accept header.  (See `RFC 2616 - Sec 14.1 <http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html>`_)  Clients can also override this standard content negotiation by specifying a `_format` ...

  The :mod:`emitters` module provides the :class:`BaseEmitter` class and a set of default emitters, including emitters for JSON and XML, as well as emitters for HTML and Plain Text which provide for a self documenting API.

  The ordering of the Emitters is important as it determines an order of preference.

  Default: ``(emitters.JSONEmitter, emitters.DocumentingHTMLEmitter, emitters.DocumentingXHTMLEmitter, emitters.DocumentingPlainTextEmitter, emitters.XMLEmitter)``

.. attribute:: Resource.parsers

  Lists the set of parsers that the Resource supports. This determines which media types the resource can accept as input for incoming HTTP requests.  (Typically PUT and POST requests).

  The ordering of the Parsers may be considered informative of preference but is not used ...

  Default: ``(parsers.JSONParser, parsers.XMLParser, parsers.FormParser)``

.. attribute:: Resource.form

  If not None, this attribute should be a Django form which will be used to validate any request data.
  This attribute is typically only used for POST or PUT requests to the resource.

  Deafult: ``None``

.. attribute:: Resource.callmap

  Maps HTTP methods to function calls on the :class:`Resource`.  It may be overridden in order to add support for other HTTP methods such as HEAD, OPTIONS and PATCH, or in order to map methods to different function names, for example to use a more `CRUD <http://en.wikipedia.org/wiki/Create,_read,_update_and_delete>`_ like style.

  Default:  ``{ 'GET': 'get', 'POST': 'post', 'PUT': 'put', 'DELETE': 'delete' }``


:class:`Resource` methods
-------------------------

.. method:: Resource.get
.. method:: Resource.post
.. method:: Resource.put
.. method:: Resource.delete
.. method:: Resource.authenticate
.. method:: Resource.reverse

:class:`Resource` properties
----------------------------

.. method:: Resource.name
.. method:: Resource.description
.. method:: Resource.default_emitter
.. method:: Resource.default_parser
.. method:: Resource.emitted_media_types
.. method:: Resource.parsed_media_types

:class:`Resource` reserved parameters
-------------------------------------

.. attribute:: Resource.ACCEPT_QUERY_PARAM

  If set, allows the default `Accept:` header content negotiation to be bypassed by setting the requested media type in a query parameter on the URL.  This can be useful if it is necessary to be able to hyperlink to a given format on the Resource using standard HTML.

  Set to None to disable, or to another string value to use another name for the reserved URL query parameter.

  Default: ``_accept``

.. attribute:: Resource.METHOD_PARAM

  If set, allows for PUT and DELETE requests to be tunneled on form POST operations, by setting a (typically hidden) form field with the method name.  This allows standard HTML forms to perform method requests which would otherwise `not be supported <http://dev.w3.org/html5/spec/Overview.html#attr-fs-method>`_

  Set to None to disable, or to another string value to use another name for the reserved form field.

  Default: ``_method``

.. attribute:: Resource.CONTENTTYPE_PARAM

  Used together with :attr:`CONTENT_PARAM`.

  If set, allows for arbitrary content types to be tunneled on form POST operations, by setting a form field with the content type.  This allows standard HTML forms to perform requests with content types other those `supported by default <http://dev.w3.org/html5/spec/Overview.html#attr-fs-enctype>`_ (ie. `application/x-www-form-urlencoded`, `multipart/form-data`, and `text-plain`)
  
  Set to None to disable, or to another string value to use another name for the reserved form field.

  Default: ``_contenttype``

.. attribute:: Resource.CONTENT_PARAM

  Used together with :attr:`CONTENTTYPE_PARAM`.

  Set to None to disable, or to another string value to use another name for the reserved form field.

  Default: ``_content``

.. attribute:: Resource.CSRF_PARAM

  The name used in Django's (typically hidden) form field for `CSRF Protection <http://docs.djangoproject.com/en/dev/ref/contrib/csrf/>`_.

  Setting to None does not disable Django's CSRF middleware, but it does mean that the field name will not be treated as reserved by FlyWheel, so for example the default :class:`FormParser` will return fields with this as part of the request content, rather than ignoring them.

  Default:: ``csrfmiddlewaretoken``

reserved params
internal methods
