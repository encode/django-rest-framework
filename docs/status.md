Status Codes
============

> 418 I'm a teapot - Any attempt to brew coffee with a teapot should result in the error code "418 I'm a teapot". The resulting entity body MAY be short and stout.
 - RFC 2324

REST framework provides a ...
These are simply ...

    from djangorestframework import status

    def view(self):
        return Response(status=status.HTTP_404_NOT_FOUND)

For more information see [RFC 2616](1).

[1]: http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html