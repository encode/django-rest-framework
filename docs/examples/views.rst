Getting Started - Views
-----------------------

.. note::

    A live sandbox instance of this API is available:
    
    http://rest.ep.io/resource-example/

    You can browse the API using a web browser, or from the command line::

        curl -X GET http://rest.ep.io/resource-example/ -H 'Accept: text/plain'

We're going to start off with a simple example, that demonstrates a few things:

#. Creating views.
#. Linking views.
#. Writing method handlers on views.
#. Adding form validation to views.

First we'll define two views in our urlconf.

``urls.py``

.. include:: ../../examples/resourceexample/urls.py
    :literal:

Now we'll add a form that we'll use for input validation.  This is completely optional, but it's often useful.

``forms.py``

.. include:: ../../examples/resourceexample/forms.py
    :literal:

Now we'll write our views.  The first is a read only view that links to three instances of the second.  The second view just has some stub handler methods to help us see that our example is working.

``views.py``

.. include:: ../../examples/resourceexample/views.py
    :literal:

That's us done.  Our API now provides both programmatic access using JSON and XML, as well a nice browseable HTML view, so we can now access it both from the browser:

* http://rest.ep.io/resource-example/

And from the command line:

.. code-block:: bash

    # Demonstrates API's input validation using form input
    bash: curl -X POST --data 'foo=true' http://rest.ep.io/resource-example/1/
    {"detail": {"bar": ["This field is required."], "baz": ["This field is required."]}}

    #  Demonstrates API's input validation using JSON input
    bash: curl -X POST -H 'Content-Type: application/json' --data-binary '{"foo":true}' http://rest.ep.io/resource-example/1/
   {"detail": {"bar": ["This field is required."], "baz": ["This field is required."]}}
