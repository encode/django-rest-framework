.. _modelresources:

Getting Started - Model Resources
---------------------------------

.. note::

    A live sandbox instance of this API is available:
    
    http://api.django-rest-framework.org/model-resource-example/

    You can browse the API using a web browser, or from the command line::

        curl -X GET http://api.django-rest-framework.org/resource-example/ -H 'Accept: text/plain'

Often you'll want parts of your API to directly map to existing django models.  Django REST framework handles this nicely for you in a couple of ways:

#. It automatically provides suitable create/read/update/delete methods for your resources.
#. Input validation occurs automatically, by using appropriate `ModelForms <http://docs.djangoproject.com/en/dev/topics/forms/modelforms/>`_.

We'll start of defining two resources in our urlconf again.

``urls.py``

.. include:: ../../examples/modelresourceexample/urls.py
    :literal:

Here's the models we're working from in this example.  It's usually a good idea to make sure you provide the :func:`get_absolute_url()` `permalink <http://docs.djangoproject.com/en/dev/ref/models/instances/#get-absolute-url>`_ for all models you want to expose via the API.

``models.py``

.. include:: ../../examples/modelresourceexample/models.py
    :literal:

Now that we've got some models and a urlconf, there's very little code to write.  We'll create a :class:`.ModelResource` to map to instances of our models, and a top level :class:`.RootModelResource` to list the existing instances and to create new instances.

``views.py``

.. include:: ../../examples/modelresourceexample/views.py
    :literal:

And we're done.  We've now got a fully browseable API, which supports multiple input and output media types, and has all the nice automatic field validation that Django gives us for free.

We can visit the API in our browser:

* http://api.django-rest-framework.org/model-resource-example/

Or access it from the command line using curl:

.. code-block:: bash

    #  Demonstrates API's input validation using form input
    bash: curl -X POST --data 'foo=true' http://api.django-rest-framework.org/model-resource-example/
    {"detail": {"bar": ["This field is required."], "baz": ["This field is required."]}}

    #  Demonstrates API's input validation using JSON input
    bash: curl -X POST -H 'Content-Type: application/json' --data-binary '{"foo":true}' http://api.django-rest-framework.org/model-resource-example/
   {"detail": {"bar": ["This field is required."], "baz": ["This field is required."]}}

We could also have added the handler methods :meth:`.Resource.get()`, :meth:`.Resource.post()` etc... seen in the last example, but Django REST framework provides nice default implementations for us that do exactly what we'd expect them to. 
