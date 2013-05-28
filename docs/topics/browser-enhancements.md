# Browser enhancements

> "There are two noncontroversial uses for overloaded POST.  The first is to *simulate* HTTP's uniform interface for clients like web browsers that don't support PUT or DELETE"
>
> &mdash; [RESTful Web Services][cite], Leonard Richardson & Sam Ruby.

## Browser based PUT, DELETE, etc...

REST framework supports browser-based `PUT`, `DELETE` and other methods, by
overloading `POST` requests using a hidden form field.

Note that this is the same strategy as is used in [Ruby on Rails][rails].

For example, given the following form:

    <form action="/news-items/5" method="POST">
        <input type="hidden" name="_method" value="DELETE">
    </form>

`request.method` would return `"DELETE"`.

## HTTP header based method overriding

REST framework also supports method overriding via the semi-standard `X-HTTP-Method-Override` header.  This can be useful if you are working with non-form content such as JSON and are working with an older web server and/or hosting provider that doesn't recognise particular HTTP methods such as `PATCH`.  For example [Amazon Web Services ELB][aws_elb].

To use it, make a `POST` request, setting the `X-HTTP-Method-Override` header.

For example, making a `PATCH` request via `POST` in jQuery:

	$.ajax({
		url: '/myresource/',
		method: 'POST',
		headers: {'X-HTTP-Method-Override': 'PATCH'},
		...
	});

## Browser based submission of non-form content

Browser-based submission of content types other than form are supported by
using form fields named `_content` and `_content_type`:

For example, given the following form:

    <form action="/news-items/5" method="PUT">
        <input type="hidden" name="_content_type" value="application/json">
        <input name="_content" value="{'count': 1}">
    </form>

`request.content_type` would return `"application/json"`, and
`request.stream` would return `"{'count': 1}"`

## URL based accept headers

REST framework can take `?accept=application/json` style URL parameters,
which allow the `Accept` header to be overridden.

This can be useful for testing the API from a web browser, where you don't
have any control over what is sent in the `Accept` header.

## URL based format suffixes

REST framework can take `?format=json` style URL parameters, which can be a
useful shortcut for determining which content type should be returned from
the view.

This is a more concise than using the `accept` override, but it also gives
you less control.  (For example you can't specify any media type parameters)

## Doesn't HTML5 support PUT and DELETE forms?

Nope.  It was at one point intended to support `PUT` and `DELETE` forms, but
was later [dropped from the spec][html5].  There remains
[ongoing discussion][put_delete] about adding support for `PUT` and `DELETE`,
as well as how to support content types other than form-encoded data.

[cite]: http://www.amazon.com/Restful-Web-Services-Leonard-Richardson/dp/0596529260
[rails]: http://guides.rubyonrails.org/form_helpers.html#how-do-forms-with-put-or-delete-methods-work
[html5]: http://www.w3.org/TR/html5-diff/#changes-2010-06-24
[put_delete]: http://amundsen.com/examples/put-delete-forms/
[aws_elb]: https://forums.aws.amazon.com/thread.jspa?messageID=400724
