Getting Started - Model Views
-----------------------------

.. note::

    A live sandbox instance of this API is available:
    
    http://rest.ep.io/model-resource-example/

    You can browse the API using a web browser, or from the command line::

        curl -X GET http://rest.ep.io/resource-example/ -H 'Accept: text/plain'

Often you'll want parts of your API to directly map to existing django models.  Django REST framework handles this nicely for you in a couple of ways:

#. It automatically provides suitable create/read/update/delete methods for your views.
#. Input validation occurs automatically, by using appropriate `ModelForms <http://docs.djangoproject.com/en/dev/topics/forms/modelforms/>`_.

Here's the model we're working from in this example:

``models.py``

.. include:: ../../examples/modelresourceexample/models.py
    :literal:

To add an API for the model, first we need to create a Resource for the model.

``resources.py``

.. include:: ../../examples/modelresourceexample/resources.py
    :literal:

Then we simply map a couple of views to the Resource in our urlconf.

``urls.py``

.. include:: ../../examples/modelresourceexample/urls.py
    :literal:

And we're done.  We've now got a fully browseable API, which supports multiple input and output media types, and has all the nice automatic field validation that Django gives us for free.

We can visit the API in our browser:

* http://rest.ep.io/model-resource-example/

Or access it from the command line using curl:

.. code-block:: bash

    #  Demonstrates API's input validation using form input
    bash: curl -X POST --data 'foo=true' http://rest.ep.io/model-resource-example/
    {"detail": {"bar": ["This field is required."], "baz": ["This field is required."]}}

    #  Demonstrates API's input validation using JSON input
    bash: curl -X POST -H 'Content-Type: application/json' --data-binary '{"foo":true}' http://rest.ep.io/model-resource-example/
   {"detail": {"bar": ["This field is required."], "baz": ["This field is required."]}}
