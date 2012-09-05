# Returning URIs from your Web APIs

> The central feature that distinguishes the REST architectural style from other network-based styles is its emphasis on a uniform interface between components.
>
> &mdash; Roy Fielding, [Architectural Styles and the Design of Network-based Software Architectures][cite]

As a rule, it's probably better practice to return absolute URIs from you web APIs, such as `http://example.com/foobar`, rather than returning relative URIs, such as `/foobar`.

The advantages of doing so are:

* It's more explicit.
* It leaves less work for your API clients.
* There's no ambiguity about the meaning of the string when it's found in representations such as JSON that do not have a native URI type.
* It allows use to easily do things like markup HTML representations with hyperlinks.

REST framework provides two utility functions to make it more simple to return absolute URIs from your Web API.

There's no requirement for you to use them, but if you do then the self-describing API will be able to automatically hyperlink it's output for you, which makes browsing the API much easier.

## reverse(viewname, request, *args, **kwargs)

Has the same behavior as [`django.core.urlresolvers.reverse`][reverse], except that it returns a fully qualified URL, using the request to determine the host and port.

    from djangorestframework.utils import reverse
    from djangorestframework.views import APIView
   
	class MyView(APIView):
	    def get(self, request):
			content = {
 				...
    		    'url': reverse('year-summary', request, args=[1945])
            }
    		return Response(content)

## reverse_lazy(viewname, request, *args, **kwargs)

Has the same behavior as [`django.core.urlresolvers.reverse_lazy`][reverse-lazy], except that it returns a fully qualified URL, using the request to determine the host and port.

[cite]: http://www.ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm#sec_5_1_5
[reverse]: https://docs.djangoproject.com/en/dev/topics/http/urls/#reverse
[reverse-lazy]: https://docs.djangoproject.com/en/dev/topics/http/urls/#reverse-lazy