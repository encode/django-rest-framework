Serializers
===========

> Expanding the usefulness of the serializers is something that we would
like to address. However, it's not a trivial problem, and it
will take some serious design work. Any offers to help out in this
area would be gratefully accepted.
 - Russell Keith-Magee, [Django users group][1]

Serializers provide a way of filtering the content of responses, prior to the response being rendered.

They also allow us to use complex data such as querysets and model instances for the content of our responses, and convert that data into native python datatypes that can then be easily rendered into `JSON`, `XML` or whatever.

REST framework includes a default `Serializer` class which gives you a powerful, generic way to control the output of your responses, but you can also write custom serializers for your data, or create other generic serialization strategies to suit the needs of your API.

BaseSerializer
--------------

This is the base class for all serializers.  If you want to provide your own custom serialization, override this class.

.serialize()
------------

Serializer
----------

This is the default serializer.

fields
------

include
-------

exclude
-------

rename
------

related_serializer
------------------

depth
-----

[1]: https://groups.google.com/d/topic/django-users/sVFaOfQi4wY/discussion
