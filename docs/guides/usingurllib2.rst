Using urllib2 with Django REST Framework
========================================

Python's standard library comes with some nice modules
you can use to test your api or even write a full client.

Using the 'GET' method
----------------------

Here's an example which does a 'GET' on the `model-resource` example
in the sandbox.::

    >>> import urllib2
    >>> r = urllib2.urlopen('htpp://rest.ep.io/model-resource-example')
    >>> r.getcode() # Check if the response was ok
    200
    >>> print r.read() # Examin the response itself
    [{"url": "http://rest.ep.io/model-resource-example/1/", "baz": "sdf", "foo": true, "bar": 123}]

Using the 'POST' method
-----------------------

And here's an example which does a 'POST' to create a new instance. First let's encode 
the data we want to POST. We'll use `urllib` for encoding and the `time` module 
to send the current time as as a string value for our POST.::

    >>> import urllib, time
    >>> d = urllib.urlencode((('bar', 123), ('baz', time.asctime())))
   
Now use the `Request` class and specify the 'Content-type'::

    >>> req = urllib2.Request('http://rest.ep.io/model-resource-example/', data=d, headers={'Content-Type':'application/x-www-form-urlencoded'})
    >>> resp = urllib2.urlopen(req)
    >>> resp.getcode()
    201
    >>> resp.read()
    '{"url": "http://rest.ep.io/model-resource-example/4/", "baz": "Fri Dec 30 18:22:52 2011", "foo": false, "bar": 123}'

That should get you started to write a client for your own api.
