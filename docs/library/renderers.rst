:mod:`renderers`
================

The renderers module provides a set of renderers that can be plugged in to a :class:`.Resource`.  
A renderer is responsible for taking the output of a View and serializing it to a given media type.  
A :class:`.Resource` can have a number of renderers, allow the same content to be serialized in a number
of different formats depending on the requesting client's preferences, as specified in the HTTP Request's Accept header.

.. automodule:: renderers
   :members:
