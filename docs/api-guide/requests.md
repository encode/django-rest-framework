<a class="github" href="request.py"></a>

# Requests

> If you're doing REST-based web service stuff ... you should ignore request.POST.
>
> — Malcom Tredinnick, [Django developers group][cite]

REST framework's `Request` class extends the standard `HttpRequest`, adding support for parsing multiple content types, allowing browser-based `PUT`, `DELETE` and other methods, and adding flexible per-request authentication.

## .method

`request.method` returns the uppercased string representation of the request's HTTP method.

Browser-based `PUT`, `DELETE` and other requests are supported, and can be made by using a hidden form field named `_method` in a regular `POST` form.



## .content_type

`request.content`, returns a string object representing the mimetype of the HTTP request's body, if one exists.



## .DATA

`request.DATA` returns the parsed content of the request body.  This is similar to the standard `HttpRequest.POST` attribute except that:

1. It supports parsing the content of HTTP methods other than `POST`, meaning that you can access the content of `PUT` and `PATCH` requests.
2. It supports parsing multiple content types, rather than just form data.  For example you can handle incoming json data in the same way that you handle incoming form data.

## .FILES

`request.FILES` returns any uploaded files that may be present in the content of the request body.  This is the same as the standard `HttpRequest` behavior, except that the same flexible request parsing that is used for `request.DATA`.

This allows you to support file uploads from multiple content-types.  For example you can write a parser that supports `POST`ing the raw content of a file, instead of using form-encoded file uploads.

## .user

`request.user` returns a `django.contrib.auth.models.User` instance. 

## .auth

`request.auth` returns any additional authentication context that may not be contained in `request.user`.  The exact behavior of `request.auth` depends on what authentication has been set in `request.authentication`.  For many types of authentication this will simply be `None`, but it may also be an object representing a permission scope, an expiry time, or any other information that might be contained in a token-based authentication scheme.

## .parsers

`request.parsers` should be set to a list of `Parser` instances that can be used to parse the content of the request body.

`request.parsers` may no longer be altered once `request.DATA`, `request.FILES` or `request.POST` have been accessed.

If you're using the `djangorestframework.views.View` class... **[TODO]**

## .stream

`request.stream` returns a stream representing the content of the request body.

You will not typically need to access `request.stream`, unless you're writing a `Parser` class.

## .authentication

`request.authentication` should be set to a list of `Authentication` instances that can be used to authenticate the request.

`request.authentication` may no longer be altered once `request.user` or `request.auth` have been accessed.

If you're using the `djangorestframework.views.View` class... **[TODO]**

[cite]: https://groups.google.com/d/topic/django-developers/dxI4qVzrBY4/discussion