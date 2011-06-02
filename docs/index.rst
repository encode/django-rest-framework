.. meta::
   :description: A lightweight REST framework for Django.
   :keywords: django, python, REST, RESTful, API, interface, framework


Django REST framework
=====================

Introduction
------------

Django REST framework is a lightweight REST framework for Django, that aims to make it easy to build well-connected, self-describing RESTful Web APIs.

**Browse example APIs created with Django REST framework:** `The Sandbox <http://api.django-rest-framework.org/>`_ 

Features:

* Automatically provides an awesome Django admin style `browse-able self-documenting API <http://api.django-rest-framework.org>`_.
* Clean, simple, views for Resources, using Django's new `class based views <http://docs.djangoproject.com/en/dev/topics/class-based-views/>`_.
* Support for ModelResources with out-of-the-box default implementations and input validation.
* Pluggable :mod:`.parsers`, :mod:`renderers`, :mod:`authentication` and :mod:`permissions` - Easy to customise.
* Content type negotiation using HTTP Accept headers.
* Optional support for forms as input validation.
* Modular architecture - MixIn classes can be used without requiring the :class:`.Resource` or :class:`.ModelResource` classes.

Resources
---------

**Project hosting:** `Bitbucket <https://bitbucket.org/tomchristie/django-rest-framework>`_ and `GitHub <https://github.com/tomchristie/django-rest-framework>`_.

* The ``djangorestframework`` package is `available on PyPI <http://pypi.python.org/pypi/djangorestframework>`_.
* We have an active `discussion group <http://groups.google.com/group/django-rest-framework>`_ and a `project blog <http://blog.django-rest-framework.org>`_. 
* Bug reports are handled on the `issue tracker <https://github.com/tomchristie/django-rest-framework/issues>`_.
* There is a `Jenkins CI server <http://datacenter.tibold.nl/job/djangorestframework/>`_ which tracks test status and coverage reporting.  (Thanks Marko!)

Any and all questions, thoughts, bug reports and contributions are *hugely appreciated*.

Requirements
------------

* Python (2.5, 2.6, 2.7 supported)
* Django (1.2, 1.3 supported)


Installation
------------


You can install Django REST framework using ``pip`` or ``easy_install``::

    pip install djangorestframework

Or get the latest development version using mercurial or git::

    hg clone https://bitbucket.org/tomchristie/django-rest-framework
    git clone git@github.com:tomchristie/django-rest-framework.git

Or you can `download the current release <http://pypi.python.org/pypi/djangorestframework>`_.

Setup
-----

To add Django REST framework to a Django project:

* Ensure that the ``djangorestframework`` directory is on your ``PYTHONPATH``.
* Add ``djangorestframework`` to your ``INSTALLED_APPS``.

For more information on settings take a look at the :ref:`setup` section.

Getting Started
---------------

Using Django REST framework can be as simple as adding a few lines to your urlconf and adding a `permalink <http://docs.djangoproject.com/en/dev/ref/models/instances/#get-absolute-url>`_ to your model.

`urls.py`::

    from django.conf.urls.defaults import patterns, url
    from djangorestframework import ModelResource, RootModelResource
    from models import MyModel

    urlpatterns = patterns('',
        url(r'^$', RootModelResource.as_view(model=MyModel)),
        url(r'^(?P<pk>[^/]+)/$', ModelResource.as_view(model=MyModel), name='my-model'),
     )

`models.py`::

    class MyModel(models.Model):

        # (Rest of model definition...)

        @models.permalink
        def get_absolute_url(self):
            return ('my-model', (self.pk,))

Django REST framework comes with two "getting started" examples.

#. :ref:`resources`
#. :ref:`modelresources`
	
Examples
--------

There are a few real world web API examples included with Django REST framework.

#. :ref:`objectstore` - Using :class:`.Resource` for resources that do not map to models.
#. :ref:`codehighlighting` - Using :class:`.Resource` with forms for input validation.
#. :ref:`blogposts` - Using :class:`.ModelResource` for resources that map directly to models.

All the examples are freely available for testing in the sandbox:

    http://api.django-rest-framework.org

(The :ref:`sandbox` resource is also documented.)



How Tos, FAQs & Notes
---------------------

.. toctree::
  :maxdepth: 1

  howto/setup
  howto/usingcurl
  howto/alternativeframeworks
  howto/mixin

Library Reference
-----------------

.. toctree::
  :maxdepth: 1

  library/authentication
  library/compat
  library/mixins
  library/parsers
  library/permissions
  library/renderers
  library/resource
  library/response
  library/status
  library/views

Examples Reference
------------------

.. toctree::
  :maxdepth: 1
  
  examples/resources
  examples/modelresources
  examples/objectstore
  examples/pygments
  examples/blogpost
  examples/sandbox
  howto/mixin

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

