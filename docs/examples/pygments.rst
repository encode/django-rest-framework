Code Highlighting API
=====================

This example demonstrates creating a REST API using a :class:`.Resource` with some form validation on the input.
We're going to provide a simple wrapper around the awesome `pygments <http://pygments.org/>`_ library, to create the Web API for a simple pastebin.

.. note::

    A live sandbox instance of this API is available at http://rest.ep.io/pygments/

    You can browse the API using a web browser, or from the command line::

        curl -X GET http://rest.ep.io/pygments/ -H 'Accept: text/plain'


URL configuration
-----------------

We'll need two resources:

* A resource which represents the root of the API. 
* A resource which represents an instance of a highlighted snippet.

``urls.py``

.. include:: ../../examples/pygments_api/urls.py
    :literal:

Form validation
---------------

We'll now add a form to specify what input fields are required when creating a new highlighted code snippet.  This will include:

* The code text itself.
* An optional title for the code.
* A flag to determine if line numbers should be included.
* Which programming language to interpret the code snippet as.
* Which output style to use for the highlighting.

``forms.py``

.. include:: ../../examples/pygments_api/forms.py
    :literal:

Creating the resources
----------------------

We'll need to define 3 resource handling methods on our resources.

* ``PygmentsRoot.get()`` method, which lists all the existing snippets.
* ``PygmentsRoot.post()`` method, which creates new snippets.
* ``PygmentsInstance.get()`` method, which returns existing snippets.

And set a number of attributes on our resources.

* Set the ``allowed_methods`` and ``anon_allowed_methods`` attributes on both resources allowing for full unauthenticated access.
* Set the ``form`` attribute on the ``PygmentsRoot`` resource, to give us input validation when we create snippets.
* Set the ``emitters`` attribute on the ``PygmentsInstance`` resource, so that 

``views.py``

.. include:: ../../examples/pygments_api/views.py
    :literal:

Completed
---------

And we're done.  We now have an API that is:

* **Browseable.**  The API supports media types for both programmatic and human access, and can be accessed either via a browser or from the command line.
* **Self describing.**  The API serves as it's own documentation. 
* **Well connected.** The API can be accessed fully by traversal from the initial URL.  Clients never need to construct URLs themselves.

Our API also supports multiple media types for both input and output, and applies sensible input validation in all cases.

For example if we make a POST request using form input:

.. code-block:: bash

    bash: curl -X POST --data 'code=print "hello, world!"' --data 'style=foobar' -H 'X-Requested-With: XMLHttpRequest' http://rest.ep.io/pygments/
    {"detail": {"style": ["Select a valid choice. foobar is not one of the available choices."], "lexer": ["This field is required."]}}

Or if we make the same request using JSON:

.. code-block:: bash

    bash: curl -X POST --data-binary '{"code":"print \"hello, world!\"", "style":"foobar"}' -H 'Content-Type: application/json' -H 'X-Requested-With: XMLHttpRequest' http://rest.ep.io/pygments/
    {"detail": {"style": ["Select a valid choice. foobar is not one of the available choices."], "lexer": ["This field is required."]}}

