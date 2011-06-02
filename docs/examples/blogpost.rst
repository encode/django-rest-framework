.. _blogposts:

Blog Posts API
==============

* http://api.django-rest-framework.org/blog-post/

The models
----------

In this example we're working from two related models:

``models.py``

.. include:: ../../examples/blogpost/models.py
    :literal:

Creating the resources
----------------------

Once we have some existing models there's very little we need to do to create the API.
Firstly create a resource for each model that defines which fields we want to expose on the model.
Secondly we map a base view and an instance view for each resource.
The generic views :class:`.ListOrCreateModelView` and :class:`.InstanceModelView` provide default operations for listing, creating and updating our models via the API, and also automatically provide input validation using default ModelForms for each model.

``urls.py``

.. include:: ../../examples/blogpost/urls.py
    :literal:
