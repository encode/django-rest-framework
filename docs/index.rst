.. meta::
   :description: A lightweight REST framework for Django.
   :keywords: django, python, REST, RESTful, API, interface, framework


Django REST framework
=====================

Introduction
------------

Django REST framework is a lightweight REST framework for Django, that aims to make it easy to build well-connected, self-describing RESTful Web APIs.

**Browse example APIs created with Django REST framework:** `The Sandbox <http://rest.ep.io/>`_

Features:
---------

* Automatically provides an awesome Django admin style `browse-able self-documenting API <http://rest.ep.io>`_.
* Clean, simple, views for Resources, using Django's new `class based views <http://docs.djangoproject.com/en/dev/topics/class-based-views/>`_.
* Support for ModelResources with out-of-the-box default implementations and input validation.
* Pluggable :mod:`.parsers`, :mod:`renderers`, :mod:`authentication` and :mod:`permissions` - Easy to customise.
* Content type negotiation using HTTP Accept headers.
* Optional support for forms as input validation.
* Modular architecture - MixIn classes can be used without requiring the :class:`.Resource` or :class:`.ModelResource` classes.

Resources
---------

**Project hosting:** `GitHub <https://github.com/tomchristie/django-rest-framework>`_.

* The ``djangorestframework`` package is `available on PyPI <http://pypi.python.org/pypi/djangorestframework>`_.
* We have an active `discussion group <http://groups.google.com/group/django-rest-framework>`_.
* Bug reports are handled on the `issue tracker <https://github.com/tomchristie/django-rest-framework/issues>`_.
* There is a `Jenkins CI server <http://jenkins.tibold.nl/job/djangorestframework/>`_ which tracks test status and coverage reporting.  (Thanks Marko!)

Any and all questions, thoughts, bug reports and contributions are *hugely appreciated*.

Requirements
------------

* Python (2.5, 2.6, 2.7 supported)
* Django (1.2, 1.3, 1.4-alpha supported)


Installation
------------

You can install Django REST framework using ``pip`` or ``easy_install``::

    pip install djangorestframework

Or get the latest development version using git::

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

Using Django REST framework can be as simple as adding a few lines to your urlconf.

The following example exposes your `MyModel` model through an api. It will provide two views:

 * A view which lists your model instances and simultaniously allows creation of instances 
   from that view.

 * Another view which lets you view, update or delete  your model instances individually.

``urls.py``::

    from django.conf.urls.defaults import patterns, url
    from djangorestframework.resources import ModelResource
    from djangorestframework.views import ListOrCreateModelView, InstanceModelView
    from myapp.models import MyModel

    class MyResource(ModelResource):
        model = MyModel

    urlpatterns = patterns('',
        url(r'^$', ListOrCreateModelView.as_view(resource=MyResource)),
        url(r'^(?P<pk>[^/]+)/$', InstanceModelView.as_view(resource=MyResource)),
    )

.. include:: howto.rst

.. include:: library.rst


.. include:: examples.rst

.. toctree::
  :hidden: 

  contents

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

