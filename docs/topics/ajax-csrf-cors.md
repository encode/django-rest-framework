# Working with AJAX, CSRF & CORS

> "Take a close look at possible CSRF / XSRF vulnerabilities on your own websites.  They're the worst kind of vulnerability &mdash; very easy to exploit by attackers, yet not so intuitively easy to understand for software developers, at least until you've been bitten by one."
>
>  &mdash; [Jeff Atwood][cite]

## Javascript clients

If you’re building a JavaScript client to interface with your Web API, you'll need to consider if the client can use the same authentication policy that is used by the rest of the website, and also determine if you need to use CSRF tokens or CORS headers.

AJAX requests that are made within the same context as the API they are interacting with will typically use `SessionAuthentication`.  This ensures that once a user has logged in, any AJAX requests made can be authenticated using the same session-based authentication that is used for the rest of the website.

AJAX requests that are made on a different site from the API they are communicating with will typically need to use a non-session-based authentication scheme, such as `TokenAuthentication`.

## CSRF protection

[Cross Site Request Forgery][csrf] protection is a mechanism of guarding against a particular type of attack, which can occur when a user has not logged out of a web site, and continues to have a valid session.   In this circumstance a malicious site may be able to perform actions against the target site, within the context of the logged-in session.

To guard against these type of attacks, you need to do two things:

1. Ensure that the 'safe' HTTP operations, such as `GET`, `HEAD` and `OPTIONS` cannot be used to alter any server-side state.
2. Ensure that any 'unsafe' HTTP operations, such as `POST`, `PUT`, `PATCH` and `DELETE`, always require a valid CSRF token.

If you're using `SessionAuthentication` you'll need to include valid CSRF tokens for any `POST`, `PUT`, `PATCH` or `DELETE` operations.

In order to make AJAX requests, you need to include CSRF token in the HTTP header, as [described in the Django documentation][csrf-ajax].

## CORS

[Cross-Origin Resource Sharing][cors] is a mechanism for allowing clients to interact with APIs that are hosted on a different domain.  CORS works by requiring the server to include a specific set of headers that allow a browser to determine if and when cross-domain requests should be allowed.

The best way to deal with CORS in REST framework is to add the required response headers in middleware.  This ensures that CORS is supported transparently, without having to change any behavior in your views.

[Otto Yiu][ottoyiu] maintains the [django-cors-headers] package, which is known to work correctly with REST framework APIs.

[cite]: https://blog.codinghorror.com/preventing-csrf-and-xsrf-attacks/
[csrf]: https://www.owasp.org/index.php/Cross-Site_Request_Forgery_(CSRF)
[csrf-ajax]: https://docs.djangoproject.com/en/stable/ref/csrf/#ajax
[cors]: https://www.w3.org/TR/cors/
[ottoyiu]: https://github.com/ottoyiu/
[django-cors-headers]: https://github.com/ottoyiu/django-cors-headers/
