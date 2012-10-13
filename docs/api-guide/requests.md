<a class="github" href="request.py"></a>

# Requests

> If you're doing REST-based web service stuff ... you should ignore request.POST.
>
> &mdash; Malcom Tredinnick, [Django developers group][cite]

REST framework's `Request` class extends the standard `HttpRequest`, adding support for REST framework's flexible request parsing and request authentication.

---

# Request parsing

REST framework's Request objects provide flexible request parsing that allows you to treat requests with JSON data or other media types in the same way that you would normally deal with form data.

## .DATA

`request.DATA` returns the parsed content of the request body.  This is similar to the standard `request.POST` attribute except that:

* It supports parsing the content of HTTP methods other than `POST`, meaning that you can access the content of `PUT` and `PATCH` requests.
* It supports REST framework's flexible request parsing, rather than just supporting form data.  For example you can handle incoming JSON data in the same way that you handle incoming form data.

For more details see the [parsers documentation].

## .FILES

`request.FILES` returns any uploaded files that may be present in the content of the request body.  This is the same as the standard `HttpRequest` behavior, except that the same flexible request parsing that is used for `request.DATA`.

For more details see the [parsers documentation].

## .QUERY_PARAMS

`request.QUERY_PARAMS` is a more correcly named synonym for `request.GET`.

For clarity inside your code, we recommend using `request.QUERY_PARAMS` instead of the usual `request.GET`, as *any* HTTP method type may include query parameters.

## .parsers

The `APIView` class or `@api_view` decorator will ensure that this property is automatically to a list of `Parser` instances, based on the `parser_classes` set on the view or based on the `DEFAULT_PARSERS` setting.

You won't typically need to access this property.

---

**Note:** If a client sends malformed content, then accessing `request.DATA` or `request.FILES` may raise a `ParseError`.  By default REST framework's `APIView` class or `@api_view` decorator will catch the error and return a `400 Bad Request` response.

---

# Authentication

REST framework provides flexbile, per-request authentication, that gives you the abilty to:

* Use different authentication policies for different parts of your API.
* Support the use of multiple authentication policies.
* Provide both user and token information associated with the incoming request.

## .user

`request.user` typically returns an instance of `django.contrib.auth.models.User`, although the behavior depends on the authentication policy being used.

If the request is unauthenticated the default value of `request.user` is an instance of `django.contrib.auth.models.AnonymousUser`.

For more details see the [authentication documentation].

## .auth

`request.auth` returns any additional authentication context.  The exact behavior of `request.auth` depends on the authentication policy being used, but it may typically be an instance of the token that the request was authenticated against.

If the request is unauthenticated, or if no additional context is present, the default value of `request.auth` is `None`.

For more details see the [authentication documentation].

## .authenticators

The `APIView` class or `@api_view` decorator will ensure that this property is automatically to a list of `Authentication` instances, based on the `authentication_classes` set on the view or based on the `DEFAULT_AUTHENTICATORS` setting.

You won't typically need to access this property.

---

# Browser enhancments

REST framework supports a few browser enhancments such as broser-based `PUT` and `DELETE` forms.

## .method

`request.method` returns the **uppercased** string representation of the request's HTTP method.

Browser-based `PUT` and `DELETE` forms are transparently supported.

For more information see the [browser enhancements documentation].    

## .content_type

`request.content_type`, returns a string object representing the media type of the HTTP request's body, or an empty string if no media type was provided.

You won't typically need to directly access the request's content type, as you'll normally rely on REST framework's default request parsing behavior.

If you do need to access the content type of the request you should use the `.content_type` property in preference to using `request.META.get('HTTP_CONTENT_TYPE')`, as it provides transparent support for browser-based non-form content.

For more information see the [browser enhancements documentation].    

## .stream

`request.stream` returns a stream representing the content of the request body.

You won't typically need to directly access the request's content, as you'll normally rely on REST framework's default request parsing behavior.

If you do need to access the raw content directly, you should use the `.stream` property in preference to using `request.content`, as it provides transparent support for browser-based non-form content.

For more information see the [browser enhancements documentation].    

[cite]: https://groups.google.com/d/topic/django-developers/dxI4qVzrBY4/discussion
[parsers documentation]: parsers.md
[authentication documentation]: authentication.md
[browser enhancements documentation]: ../topics/browser-enhancements.md