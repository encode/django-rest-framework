.. meta::
   :description: A lightweight REST framework for Django.
   :keywords: django, python, REST, RESTful, API, interface, framework


Django REST framework
=====================

Introduction
------------

Django REST framework is a lightweight REST framework for Django, that aims to make it easy to build well-connected, self-describing RESTful Web APIs.

**Browse example APIs created with Django REST framework:** `The Sandbox <http://shielded-mountain-6732.herokuapp.com/>`_

Features:
---------

* Automatically provides an awesome Django admin style `browse-able self-documenting API <http://shielded-mountain-6732.herokuapp.com>`_.
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
* There's a comprehensive tutorial to using REST framework and Backbone JS on `10kblogger.wordpress.com <http://10kblogger.wordpress.com/2012/05/25/a-restful-password-locker-with-django-and-backbone-js/>`_.

Any and all questions, thoughts, bug reports and contributions are *hugely appreciated*.

Requirements
------------

* Python (2.6+)
* Django (1.3+)
* `django.contrib.staticfiles`_ (or `django-staticfiles`_ for Django 1.2)
* `URLObject`_ >= 2.0.0
* `Markdown`_ >= 2.1.0 (Optional)
* `PyYAML`_ >= 3.10 (Optional)

Installation
------------

You can install Django REST framework using ``pip`` or ``easy_install``::

    pip install djangorestframework

Or get the latest development version using git::

    git clone git@github.com:tomchristie/django-rest-framework.git

Setup
-----

To add Django REST framework to a Django project:

* Ensure that the ``djangorestframework`` directory is on your ``PYTHONPATH``.
* Add ``djangorestframework`` to your ``INSTALLED_APPS``.
* Add the following to your URLconf.  (To include the REST framework Login/Logout views.)::

    urlpatterns = patterns('',
        ...
        url(r'^restframework', include('djangorestframework.urls', namespace='djangorestframework'))
    )

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

.. include:: ../CHANGELOG.rst

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _django.contrib.staticfiles: https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/
.. _django-staticfiles: http://pypi.python.org/pypi/django-staticfiles/
.. _URLObject: http://pypi.python.org/pypi/URLObject/
.. _Markdown: http://pypi.python.org/pypi/Markdown/
.. _PyYAML: http://pypi.python.org/pypi/PyYAML
