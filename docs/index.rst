.. meta::
   :description: A lightweight REST framework for Django.
   :keywords: django, python, REST, RESTful


Django REST framework
=====================

Introduction
------------

Django REST framework is a lightweight REST framework for Django.

It aims to make it easy to build well-connected, self-describing Web APIs with a minimum of fuss.

Features:

* Clean, simple, class-based views for Resources.
* Support for ModelResources with nice default implementations and input validation.
* Automatically provides a browse-able self-documenting API.
* Pluggable Emitters, Parsers and Authenticators - Easy to customise.
* Content type negotiation using Accept headers.
* Optional support for forms as input validation.
* Modular architecture - Easy to extend and modify.

Requirements
------------

* Python 2.6
* Django 1.2

.. note::

    Support for a wider range of Python & Django versions is planned, but right now django-rest-framework is only tested against these versions.

Installation & Setup
--------------------

The django-rest-framework project is hosted as a `mercurial repository on bitbucket <https://bitbucket.org/tomchristie/django-rest-framework>`_.
To get a local copy of the repository use mercurial::

    hg clone https://bitbucket.org/tomchristie/django-rest-framework

To add django-rest-framework to a django project:

* Copy or symlink the ``djangorestframework`` directory into python's ``site-packages`` directory, or otherwise ensure that the ``djangorestframework`` directory is on your ``PYTHONPATH``.
* Add ``djangorestframework`` to your ``INSTALLED_APPS``.
* Ensure the ``TEMPLATE_LOADERS`` setting contains the item ``'django.template.loaders.app_directories.Loader'``. (It will do by default, so you shouldn't normally need to do anything here.)

Getting Started - Resources
---------------------------

We're going to start off with a simple example, that demonstrates
a few things:

#. Creating resources.
#. Linking resources.
#. Writing method handlers on resources.
#. Adding form validation to resources.

First we'll define two resources in our urlconf.

``urls.py``

.. include:: ../examples/resourceexample/urls.py
    :literal:

Now we'll add a form that we'll use for input validation.  This is completely optional, but it's often useful.

``forms.py``

.. include:: ../examples/resourceexample/forms.py
    :literal:

Now we'll write our resources.  The first is a read only resource that links to three instances of the second.  The second resource just has some stub handler methods to help us see that our example is working.

``views.py``

.. include:: ../examples/resourceexample/views.py
    :literal:

That's us done.  Our API now provides both programmatic access using JSON and XML, as well a nice browseable HTML view:

* http://api.django-rest-framework.org/resource-example/

.. code-block:: bash

    # Demonstrates API's input validation using form input
    bash: curl -X POST -H 'X-Requested-With: XMLHttpRequest' --data 'foo=true' http://api.django-rest-framework.org/resource-example/1/
    {"detail": {"bar": ["This field is required."], "baz": ["This field is required."]}}

    #  Demonstrates API's input validation using JSON input
    bash: curl -X POST -H 'X-Requested-With: XMLHttpRequest' -H 'Content-Type: application/json' --data-binary '{"foo":true}' http://api.django-rest-framework.org/resource-example/1/
   {"detail": {"bar": ["This field is required."], "baz": ["This field is required."]}}

Getting Started - Model Resources
---------------------------------

Often you'll want parts of your API to directly map to existing django models.  Django REST framework handles this nicely for you in a couple of ways:

#. It automatically provides suitable create/read/update/delete methods for your resources.
#. Input validation occurs automatically, by using appropriate `ModelForms <http://docs.djangoproject.com/en/dev/topics/forms/modelforms/>`_.

We'll start of defining two resources in our urlconf again.

``urls.py``

.. include:: ../examples/modelresourceexample/urls.py
    :literal:

Here's the models we're working from in this example.  It's usually a good idea to make sure you provide the :func:`get_absolute_url()` `permalink <http://docs.djangoproject.com/en/dev/ref/models/instances/#get-absolute-url>`_ for all models you want to expose via the API.

``models.py``

.. include:: ../examples/modelresourceexample/models.py
    :literal:

Now that we've got some models and a urlconf, there's very little code to write.  We'll create a :class:`.ModelResource` to map to instances of our models, and a top level :class:`.RootModelResource` to list the existing instance and to create new instances.

``views.py``

.. include:: ../examples/modelresourceexample/views.py
    :literal:

And we're done.  We've now got a fully browseable API, which supports multiple input and output media types, and has all the nice automatic field validation that Django gives us for free.

We can visit the API in our browser:

* http://api.django-rest-framework.org/model-resource-example/

Or access it from the command line using curl:

.. code-block:: bash

    #  Demonstrates API's input validation using form input
    bash: curl -X POST -H 'X-Requested-With: XMLHttpRequest' --data 'foo=true' http://api.django-rest-framework.org/model-resource-example/
    {"detail": {"bar": ["This field is required."], "baz": ["This field is required."]}}

    #  Demonstrates API's input validation using JSON input
    bash: curl -X POST -H 'X-Requested-With: XMLHttpRequest' -H 'Content-Type: application/json' --data-binary '{"foo":true}' http://api.django-rest-framework.org/model-resource-example/
   {"detail": {"bar": ["This field is required."], "baz": ["This field is required."]}}

We could also have added the handler methods :meth:`.Resource.get()`, :meth:`.Resource.post()` etc... seen in the last example, but Django REST framework provides nice default implementations for us that do exactly what we'd expect them to. 

Examples
--------

There's a few real world examples included with django-rest-framework.
These demonstrate the following use cases:

#. Using :class:`.Resource` for resources that do not map to models.
#. Using :class:`.Resource` with forms for input validation.
#. Using :class:`.ModelResource` for resources that map directly to models.

All the examples are freely available for testing in the sandbox here: http://api.django-rest-framework.org

.. toctree::
  :maxdepth: 1

  examples/objectstore
  examples/pygments
  examples/blogpost

How Tos, FAQs & Notes
---------------------

.. toctree::
  :maxdepth: 2

  howto/usingcurl
  howto/alternativeframeworks

Library Reference
-----------------

.. toctree::
  :maxdepth: 2

  library/resource
  library/modelresource
  library/emitters
  library/parsers
  library/authenticators
  library/response


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

