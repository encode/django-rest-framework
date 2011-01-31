Django REST framework
=====================

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

    hg clone https://tomchristie@bitbucket.org/tomchristie/django-rest-framework

To add django-rest-framework to a django project:

* Copy or symlink the ``djangorestframework`` directory into python's ``site-packages`` directory, or otherwise ensure that the ``djangorestframework`` directory is on your ``PYTHONPATH``.
* Add ``djangorestframework`` to your ``INSTALLED_APPS``.
* Ensure the ``TEMPLATE_LOADERS`` setting contains the item ``'django.template.loaders.app_directories.Loader'``. (It will do by default, so you shouldn't normally need to do anything here.)

Getting Started
---------------

Often you'll want parts of your API to directly map to existing Models.
Typically that might look this looks something like this...

``models.py``

.. code-block:: python

    from django.db import models

    class MyModel(models.Model):
        foo = models.BooleanField()
        bar = models.IntegerField(help_text='Must be an integer.')
        baz = models.CharField(max_length=32, help_text='Free text.  Max length 32 chars.')
        created = models.DateTimeField(auto_now_add=True)
    
        class Meta:
            ordering = ('created',)
    
        @models.permalink
        def get_absolute_url(self):
            return ('simpleexample.views.MyModelResource', (self.pk,))

``urls.py``

.. include:: ../examples/simpleexample/urls.py
    :literal:

``views.py``

.. include:: ../examples/simpleexample/views.py
    :literal:

And we're done.  We've now got a fully browseable API, which supports multiple input and output media types, and has all the nice automatic field validation that Django gives us for free.

We can visit the API in our browser:

* http://api.django-rest-framework.org/simple-example/

Or access it from the command line using curl:

.. code-block:: bash

    bash: curl -X POST -H 'X-Requested-With: XMLHttpRequest' --data 'foo=testing' http://api.django-rest-framework.org/simple-example/
    {"detail": {"bar": ["This field is required."], "baz": ["This field is required."]}}

    bash: curl -X POST -H 'X-Requested-With: XMLHttpRequest' -H 'Content-Type: application/json' --data-binary '{"foo":"testing"}' http://api.django-rest-framework.org/simple-example/
   {"detail": {"bar": ["This field is required."], "baz": ["This field is required."]}}

.. note::

  TODO: Mention adding custom handler methods, but that the defaults will often do what we want already.  Document a Resource example, not tied to models.  

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

