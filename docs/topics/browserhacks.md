# Browser hacks

> "There are two noncontroversial uses for overloaded POST.  The first is to *simulate* HTTP's uniform interface for clients like web browsers that don't support PUT or DELETE"
>
> &mdash; [RESTful Web Services](1), Leonard Richardson & Sam Ruby.

## Browser based PUT, DELETE, etc...

**TODO: Preamble.**  Note that this is the same strategy as is used in [Ruby on Rails](2).

For example, given the following form:

    <form action="/news-items/5" method="POST">
	    <input type="hidden" name="_method" value="DELETE">
	</form>

`request.method` would return `"DELETE"`.

## Browser based submission of non-form content

Browser-based submission of content types other than form are supported by using form fields named `_content` and `_content_type`:

For example, given the following form:

    <form action="/news-items/5" method="PUT">
	    <input type="hidden" name="_content_type" value="application/json">
		<input name="_content" value="{'count': 1}">
	</form>

`request.content_type` would return `"application/json"`, and `request.content` would return `"{'count': 1}"`

## URL based accept headers

## URL based format suffixes

## Doesn't HTML5 support PUT and DELETE forms?

Nope.  It was at one point intended to support `PUT` and `DELETE` forms, but was later [dropped from the spec](3).  There remains [ongoing discussion](4) about adding support for `PUT` and `DELETE`, as well as how to support content types other than form-encoded data.

[1]: http://www.amazon.com/Restful-Web-Services-Leonard-Richardson/dp/0596529260
[2]: http://guides.rubyonrails.org/form_helpers.html#how-do-forms-with-put-or-delete-methods-work
[3]: http://www.w3.org/TR/html5-diff/#changes-2010-06-24
[4]: http://amundsen.com/examples/put-delete-forms/
