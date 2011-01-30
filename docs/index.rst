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

Installation & Setup
--------------------

The django-rest-framework project is hosted as a `mercurial repository on bitbucket <https://bitbucket.org/tomchristie/flywheel>`_.
To get a local copy of the repository use mercurial::

    hg clone https://tomchristie@bitbucket.org/tomchristie/flywheel

To add django-rest-framework to a django project:

* Copy or symlink the ``djangorestframework`` directory into python's ``site-packages`` directory, or otherwise ensure that the ``djangorestframework`` directory is on your ``PYTHONPATH``.
* Add ``djangorestframework`` to your ``INSTALLED_APPS``.
* Ensure the ``TEMPLATE_LOADERS`` setting contains the item ``'django.template.loaders.app_directories.Loader'``. (It will do by default, so you shouldn't normally need to do anything here.)

Getting Started
---------------

Often you'll want parts of your API to directly map to existing Models.
At it's simplest this looks something like this...

``views.py``::

    from djangorestframework.modelresource import ModelResource, ModelRootResource
    from models import MyModel

    class MyModelRootResource(ModelRootResource):
	"""A create/list resource for MyModel."""
        allowed_methods = ('GET', 'POST')
        model = MyModel

    class MyModelResource(ModelResource):
	"""A read/update/delete resource for MyModel."""
        allowed_methods = ('GET', 'PUT', 'DELETE')
        model = MyModel

``urls.py``::

    urlpatterns += patterns('myapp.views',
        url(r'^mymodel/$',         'MyModelRootResource'), 
        url(r'^mymodel/([^/]+)/$', 'MyModelResource'), 
    )


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

