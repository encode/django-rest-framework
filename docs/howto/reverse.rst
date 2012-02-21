Returning URIs from your Web APIs
=================================

    "The central feature that distinguishes the REST architectural style from
    other network-based styles is its emphasis on a uniform interface between
    components."

    -- Roy Fielding, Architectural Styles and the Design of Network-based Software Architectures

As a rule, it's probably better practice to return absolute URIs from you web APIs, e.g. "http://example.com/foobar", rather than returning relative URIs, e.g. "/foobar".

The advantages of doing so are:

* It's more explicit.
* It leaves less work for your API clients.
* There's no ambiguity about the meaning of the string when it's found in representations such as JSON that do not have a native URI type.
* It allows us to easily do things like markup HTML representations with hyperlinks.

Django REST framework provides two utility functions to make it simpler to return absolute URIs from your Web API.

There's no requirement for you to use them, but if you do then the self-describing API will be able to automatically hyperlink its output for you, which makes browsing the API much easier.

reverse(viewname, request, ...)
-------------------------------

The :py:func:`~utils.reverse` function has the same behavior as :py:func:`django.core.urlresolvers.reverse` [1]_, except that it takes a request object and returns a fully qualified URL, using the request to determine the host and port::

    from djangorestframework.utils import reverse
    from djangorestframework.views import View
   
    class MyView(View):
        def get(self, request):
            context = {
                'url': reverse('year-summary', request, args=[1945])
            }

            return Response(context)

reverse_lazy(viewname, request, ...)
------------------------------------

The :py:func:`~utils.reverse_lazy` function has the same behavior as :py:func:`django.core.urlresolvers.reverse_lazy` [2]_, except that it takes a request object and returns a fully qualified URL, using the request to determine the host and port.

.. rubric:: Footnotes

.. [1] https://docs.djangoproject.com/en/dev/topics/http/urls/#reverse
.. [2] https://docs.djangoproject.com/en/dev/topics/http/urls/#reverse-lazy
