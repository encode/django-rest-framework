:mod:`authenticators`
=====================

.. module:: authenticators

The authenticators module provides a standard set of authentication methods that can be plugged in to a :class:`Resource`, as well as providing a template by which to write custom authentication methods.

The base class
--------------

All authenticators must subclass the :class:`BaseAuthenticator` class and override it's :func:`authenticate` method.

.. class:: BaseAuthenticator

   .. method:: authenticate(request)

      Authenticate the request and return the authentication context or None.

      The default permission checking on :class:`.Resource` will use the allowed_methods attribute for permissions if the authentication context is not None, and use anon_allowed_methods otherwise.

      The authentication context is passed to the method calls (eg :meth:`.Resource.get`, :meth:`.Resource.post` etc...) in order to allow them to apply any more fine grained permission checking at the point the response is being generated.

      This function must be overridden to be implemented.

Provided authenticators
-----------------------

