.. meta::
   :description: A lightweight REST framework for Django.
   :keywords: django, python, REST, RESTful, API, interface, framework


Django REST framework
=====================

Introduction
------------

Django REST framework aims to make it easy to build well-connected, self-describing Web APIs.

Features:

* Automatically provides a Django admin style `browse-able self-documenting API <http://api.django-rest-framework.org>`_.
* Clean, simple, views for Resources, using Django's new `class based views <http://docs.djangoproject.com/en/dev/topics/class-based-views/>`_.
* Support for ModelResources with out-of-the-box default implementations and input validation.
* Pluggable :mod:`.emitters`, :mod:`parsers`, :mod:`validators` and :mod:`authenticators` - Easy to customise.
* Content type negotiation using HTTP Accept headers.
* Optional support for forms as input validation.
* Modular architecture - MixIn classes can be used without requiring the :class:`.Resource` or :class:`.ModelResource` classes.

The django-rest-framework project is hosted as a `mercurial repository on bitbucket <https://bitbucket.org/tomchristie/django-rest-framework>`_.

For questions, thoughts and feedback please head on over to the `discussion group <http://groups.google.com/group/django-rest-framework>`_.

Bug reports are greatful received on the `issue tracker <https://bitbucket.org/tomchristie/django-rest-framework/issues?sort=version>`_.

If you're feeling particularly enthusiastic there's even a `blog <http://blog.django-rest-framework.org>`_ which I might post useful stuff to now and then.

Requirements
------------

* Python (2.5, 2.6, 2.7 supported)
* Django (1.2, 1.3 supported)


Installation & Setup
--------------------


You can install Django REST framework using ``pip`` or ``easy_install``::

    pip install djangorestframework

Or download the current release from BitBucket:

* `django-rest-framework-0.1.tar.gz <https://bitbucket.org/tomchristie/django-rest-framework/downloads/django-rest-framework-0.1.tar.gz>`_
* `django-rest-framework-0.1.zip <https://bitbucket.org/tomchristie/django-rest-framework/downloads/django-rest-framework-0.1.zip>`_

Or get the latest development version using mercurial::

    hg clone https://bitbucket.org/tomchristie/django-rest-framework

To install Django REST framework to your ``site-packages`` directory, run the ``setup.py`` script::

    python setup.py install

To add django-rest-framework to a Django project:

    * Ensure that the ``djangorestframework`` directory is on your ``PYTHONPATH``.
    * Add ``djangorestframework`` to your ``INSTALLED_APPS``.

For more information take a look at the :ref:`setup` section.

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

  library/resource
  library/modelresource
  library/emitters
  library/parsers
  library/authenticators
  library/validators
  library/response
  library/status

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

