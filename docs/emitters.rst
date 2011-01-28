:mod:`emitters`
===============

The emitters module provides a set of emitters that can be plugged in to a :class:`.Resource`.  An emitter is responsible for taking the output of a and serializing it to a given media type.  A :class:`.Resource` can have a number of emitters, allow the same content to be serialized in a number of different formats depending on the requesting client's preferences, as specified in the HTTP Request's Accept header.

.. automodule:: emitters
   :members:
