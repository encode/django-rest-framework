<a class="github" href="exceptions.py"></a>

# Exceptions

> Exceptions… allow error handling to be organized cleanly in a central or high-level place within the program structure.
>
> &mdash; Doug Hellmann, [Python Exception Handling Techniques][cite]

## Exception handling in REST framework views

REST framework's views handle various exceptions, and deal with returning appropriate error responses.

The handled exceptions are:

* Subclasses of `APIException` raised inside REST framework.
* Django's `Http404` exception.
* Django's `PermissionDenied` exception.

In each case, REST framework will return a response with an appropriate status code and content-type.  The body of the response will include any additional details regarding the nature of the error.

By default all error responses will include a key `details` in the body of the response, but other keys may also be included.

For example, the following request:

    DELETE http://api.example.com/foo/bar HTTP/1.1
    Accept: application/json

Might receive an error response indicating that the `DELETE` method is not allowed on that resource:

    HTTP/1.1 405 Method Not Allowed
    Content-Type: application/json; charset=utf-8
    Content-Length: 42
    
    {"detail": "Method 'DELETE' not allowed."}

---

# API Reference

## APIException

**Signature:** `APIException(detail=None)`

The **base class** for all exceptions raised inside REST framework.

To provide a custom exception, subclass `APIException` and set the `.status_code` and `.detail` properties on the class.

## ParseError

**Signature:** `ParseError(detail=None)`

Raised if the request contains malformed data when accessing `request.DATA` or `request.FILES`.

By default this exception results in a response with the HTTP status code "400 Bad Request".

## PermissionDenied

**Signature:** `PermissionDenied(detail=None)`

Raised when an incoming request fails the permission checks.

By default this exception results in a response with the HTTP status code "403 Forbidden".

## MethodNotAllowed

**Signature:** `MethodNotAllowed(method, detail=None)`

Raised when an incoming request occurs that does not map to a handler method on the view.

By default this exception results in a response with the HTTP status code "405 Method Not Allowed".

## UnsupportedMediaType

**Signature:** `UnsupportedMediaType(media_type, detail=None)`

Raised if there are no parsers that can handle the content type of the request data when accessing `request.DATA` or `request.FILES`.

By default this exception results in a response with the HTTP status code "415 Unsupported Media Type".

## Throttled

**Signature:** `Throttled(wait=None, detail=None)`

Raised when an incoming request fails the throttling checks.

By default this exception results in a response with the HTTP status code "429 Too Many Requests".

[cite]: http://www.doughellmann.com/articles/how-tos/python-exception-handling/index.html
