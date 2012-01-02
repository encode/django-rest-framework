Permissions
===========

This example will show how you can protect your api by using authentication
and how you can limit the amount of requests a user can do to a resource by setting
a throttle to your view.

Authentication
--------------

If you want to protect your api from unauthorized users, Django REST Framework
offers you two default authentication methods:

 * Basic Authentication
 * Django's session-based authentication

These authentication methods are by default enabled. But they are not used unless 
you specifically state that your view requires authentication. 

To do this you just need to import the `Isauthenticated` class from the frameworks' `permissions` module.::

    from djangorestframework.permissions import IsAuthenticated

Then you enable authentication by setting the right 'permission requirement' to the `permissions` class attribute of your View like
the example View below.:


.. literalinclude:: ../../examples/permissionsexample/views.py
   :pyobject: LoggedInExampleView

The `IsAuthenticated` permission will only let a user do a 'GET' if he is authenticated. Try it
yourself on the live sandbox__

__ http://rest.ep.io/permissions-example/loggedin


Throttling
----------

If you want to limit the amount of requests a client is allowed to do on 
a resource, then you can set a 'throttle' to achieve this. 

For this to work you'll need to import the `PerUserThrottling` class from the `permissions`
module.::

    from djangorestframework.permissions import PerUserThrottling

In the example below we have limited the amount of requests one 'client' or 'user' 
may do on our view to 10 requests per minute.:

.. literalinclude:: ../../examples/permissionsexample/views.py
  :pyobject: ThrottlingExampleView

Try it yourself on the live sandbox__.

__ http://rest.ep.io/permissions-example/throttling

Now if you want a view to require both aurhentication and throttling, you simply declare them
both::

    permissions = (PerUserThrottling, Isauthenticated)

To see what other throttles are available, have a look at the :mod:`permissions` module.

If you want to implement your own authentication method, then refer to the :mod:`authentication` 
module.
