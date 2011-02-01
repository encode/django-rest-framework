.. meta::
   :description: A lightweight REST framework for Django.
   :keywords: django, python, REST, RESTful


Django REST framework
=====================

Introduction
------------

A lightweight REST framework for Django.

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

Getting Started - Resource
--------------------------

We're going to start off with a simple example, that demonstrates
a few things:

* Creating resources
* Linking resources
* Writing method handlers on resources
* Adding form validation to resources

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

That's us done.

TODO


Getting Started - ModelResource
-------------------------------

Often you'll want parts of your API to directly map to existing django models.
Typically that might look this looks something like this...

``urls.py``

.. include:: ../examples/modelresourceexample/urls.py
    :literal:

``models.py``

.. include:: ../examples/modelresourceexample/models.py
    :literal:

``views.py``

.. include:: ../examples/modelresourceexample/views.py
    :literal:

And we're done.  We've now got a fully browseable API, which supports multiple input and output media types, and has all the nice automatic field validation that Django gives us for free.

We can visit the API in our browser:

* http://api.django-rest-framework.org/model-resource-example/

Or access it from the command line using curl:

.. code-block:: bash

    bash: curl -X POST -H 'X-Requested-With: XMLHttpRequest' --data 'foo=true' http://api.django-rest-framework.org/simple-example/
    {"detail": {"bar": ["This field is required."], "baz": ["This field is required."]}}

    bash: curl -X POST -H 'X-Requested-With: XMLHttpRequest' -H 'Content-Type: application/json' --data-binary '{"foo":true}' http://api.django-rest-framework.org/simple-example/
   {"detail": {"bar": ["This field is required."], "baz": ["This field is required."]}}

We could also have added the handler methods get(), post() etc... seen in the last example, but Django REST framework provides nice default implementations for us that do exactly what we'd expect them to. 

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

How Tos
-------

.. toctree::
  :maxdepth: 2

  howto/usingcurl

.. note::

    TODO

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

