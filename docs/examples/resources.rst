.. _resources:

Getting Started - Resources
---------------------------

We're going to start off with a simple example, that demonstrates a few things:

#. Creating resources.
#. Linking resources.
#. Writing method handlers on resources.
#. Adding form validation to resources.

First we'll define two resources in our urlconf.

``urls.py``

.. include:: ../../examples/resourceexample/urls.py
    :literal:

Now we'll add a form that we'll use for input validation.  This is completely optional, but it's often useful.

``forms.py``

.. include:: ../../examples/resourceexample/forms.py
    :literal:

Now we'll write our resources.  The first is a read only resource that links to three instances of the second.  The second resource just has some stub handler methods to help us see that our example is working.

``views.py``

.. include:: ../../examples/resourceexample/views.py
    :literal:

That's us done.  Our API now provides both programmatic access using JSON and XML, as well a nice browseable HTML view, so we can now access it both from the browser:

* http://api.django-rest-framework.org/resource-example/

And from the command line:

.. code-block:: bash

    # Demonstrates API's input validation using form input
    bash: curl -X POST --data 'foo=true' http://api.django-rest-framework.org/resource-example/1/
    {"detail": {"bar": ["This field is required."], "baz": ["This field is required."]}}

    #  Demonstrates API's input validation using JSON input
    bash: curl -X POST -H 'Content-Type: application/json' --data-binary '{"foo":true}' http://api.django-rest-framework.org/resource-example/1/
   {"detail": {"bar": ["This field is required."], "baz": ["This field is required."]}}
