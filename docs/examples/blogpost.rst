Blog Posts API
==============

* http://rest.ep.io/blog-post/

The models
----------

In this example we're working from two related models:

``models.py``

.. include:: ../../examples/blogpost/models.py
    :literal:

Creating the resources
----------------------

We need to create two resources that we map to our two existing models, in order to describe how the models should be serialized.
Our resource descriptions will typically go into a module called something like 'resources.py'

``resources.py``

.. include:: ../../examples/blogpost/resources.py
    :literal:

Creating views for our resources
--------------------------------

Once we've created the resources there's very little we need to do to create the API.
For each resource we'll create a base view, and an instance view.
The generic views :class:`.ListOrCreateModelView` and :class:`.InstanceModelView` provide default operations for listing, creating and updating our models via the API, and also automatically provide input validation using default ModelForms for each model.

``urls.py``

.. include:: ../../examples/blogpost/urls.py
    :literal:
