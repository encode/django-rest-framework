Using urllib2
=============

Python's standard library comes with some nice modules
you can use to test your api or even write a full client.

Here's an example which does a 'GET' on the `model-resource` examle
in the sandbox.::

    import urllib2
    >>> r = urllib2.urlopen('htpp://rest.ep.io/model-resource-example')
    # You can check if the response was ok:
    >>> r.getcode()
    200
    # Or examin the resonse itself:
    >>> print r.read()
    [{"url": "http://rest.ep.io/model-resource-example/1/", "baz": "sdf", "foo": true, "bar": 123}]

And here's an example which does a 'POST' to create a new instance::

    # First encode tha data we want to POST, we'll use urllib for encoding
    # and the time module to send the current time as as a string value for our POST
    >>> import urllib, time
    >>> d = urllib.urlencode((('bar', 123), ('baz', time.asctime())))
    # Now use the Request class and specify the 'Content-type'
    >>> req = urllib2.Request('http://rest.ep.io/model-resource-example/', data=d, headers={'Content-Type':'application/x-www-form-urlencoded'})
    >>> resp = urllib2.urlopen(req)
    >>> resp.getcode()
    201
    >>> resp.read()
    '{"url": "http://rest.ep.io/model-resource-example/4/", "baz": "Fri Dec 30 18:22:52 2011", "foo": false, "bar": 123}'

That should get you started to write a client for your own api.
