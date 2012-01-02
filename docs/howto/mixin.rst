Using Django REST framework Mixin classes
=========================================

This example demonstrates creating a REST API **without** using Django REST framework's :class:`.Resource` or :class:`.ModelResource`, but instead using Django's :class:`View` class, and adding the :class:`ResponseMixin` class to provide full HTTP Accept header content negotiation,
a browseable Web API, and much of the other goodness that Django REST framework gives you for free.

.. note::

    A live sandbox instance of this API is available for testing:
    
    * http://rest.ep.io/mixin/

    You can browse the API using a web browser, or from the command line::

        curl -X GET http://rest.ep.io/mixin/


URL configuration
-----------------

Everything we need for this example can go straight into the URL conf...

``urls.py``

.. include:: ../../examples/mixin/urls.py
    :literal:

That's it.  Auto-magically our API now supports multiple output formats, specified either by using 
standard HTTP Accept header content negotiation, or by using the `&_accept=application/json` style parameter overrides.
We even get a nice HTML view which can be used to self-document our API.
