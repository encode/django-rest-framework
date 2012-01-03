Using CURL with django-rest-framework
=====================================

`curl <http://curl.haxx.se/>`_ is a great command line tool for making requests to URLs.

There are a few things that can be helpful to remember when using CURL with django-rest-framework APIs.

#. Curl sends an ``Accept: */*`` header by default::

    curl -X GET http://example.com/my-api/

#. Setting the ``Accept:`` header on a curl request can be useful::

    curl -X GET -H 'Accept: application/json' http://example.com/my-api/

#. The text/plain representation is useful for browsing the API::

    curl -X GET -H 'Accept: text/plain' http://example.com/my-api/

#. ``POST`` and ``PUT`` requests can contain form data (ie ``Content-Type: application/x-www-form-urlencoded``)::

    curl -X PUT --data 'foo=bar' http://example.com/my-api/some-resource/

#. Or any other content type::

    curl -X PUT -H 'Content-Type: application/json' --data-binary '{"foo":"bar"}' http://example.com/my-api/some-resource/

#. You can use basic authentication to send the username and password::

    curl -X GET -H 'Accept: application/json' -u <user>:<password> http://example.com/my-api/
