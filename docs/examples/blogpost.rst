.. _blogposts:

Blog Posts API
==============

* http://api.django-rest-framework.org/blog-post/

The models
----------

``models.py``

.. include:: ../../examples/blogpost/models.py
    :literal:

URL configuration
-----------------

``urls.py``

.. include:: ../../examples/blogpost/urls.py
    :literal:

Creating the resources
----------------------

Once we have some existing models there's very little we need to do to create the corresponding resources.  We simply create a base resource and an instance resource for each model we're working with.
django-rest-framework will provide the default operations on the resources all the usual input validation that Django's models can give us for free.

``views.py``

.. include:: ../../examples/blogpost/views.py
    :literal: