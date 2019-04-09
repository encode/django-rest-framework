# Browser enhancements

> "There are two noncontroversial uses for overloaded POST.  The first is to *simulate* HTTP's uniform interface for clients like web browsers that don't support PUT or DELETE"
>
> &mdash; [RESTful Web Services][cite], Leonard Richardson & Sam Ruby.

In order to allow the browsable API to function, there are a couple of browser enhancements that REST framework needs to provide.

As of version 3.3.0 onwards these are enabled with javascript, using the [ajax-form][ajax-form] library.

## Browser based PUT, DELETE, etc...

The [AJAX form library][ajax-form] supports browser-based `PUT`, `DELETE` and other methods on HTML forms.

After including the library, use the `data-method` attribute on the form, like so:

    <form action="/" data-method="PUT">
        <input name='foo'/>
        ...
    </form>

Note that prior to 3.3.0, this support was server-side rather than javascript based. The method overloading style (as used in [Ruby on Rails][rails]) is no longer supported due to subtle issues that it introduces in request parsing.

## Browser based submission of non-form content

Browser-based submission of content types such as JSON are supported by the [AJAX form library][ajax-form], using form fields with `data-override='content-type'` and `data-override='content'` attributes.

For example:

        <form action="/">
            <input data-override='content-type' value='application/json' type='hidden'/>
            <textarea data-override='content'>{}</textarea>
            <input type="submit"/>
        </form>

Note that prior to 3.3.0, this support was server-side rather than javascript based.

## URL based format suffixes

REST framework can take `?format=json` style URL parameters, which can be a
useful shortcut for determining which content type should be returned from
the view.

This behavior is controlled using the `URL_FORMAT_OVERRIDE` setting.

## HTTP header based method overriding

Prior to version 3.3.0 the semi extension header `X-HTTP-Method-Override` was supported for overriding the request method. This behavior is no longer in core, but can be adding if needed using middleware.

For example:

    METHOD_OVERRIDE_HEADER = 'HTTP_X_HTTP_METHOD_OVERRIDE'

    class MethodOverrideMiddleware(object):
        def process_view(self, request, callback, callback_args, callback_kwargs):
            if request.method != 'POST':
                return
            if METHOD_OVERRIDE_HEADER not in request.META:
                return
            request.method = request.META[METHOD_OVERRIDE_HEADER]

## URL based accept headers

Until version 3.3.0 REST framework included built-in support for `?accept=application/json` style URL parameters, which would allow the `Accept` header to be overridden.

Since the introduction of the content negotiation API this behavior is no longer included in core, but may be added using a custom content negotiation class, if needed.

For example:

    class AcceptQueryParamOverride()
        def get_accept_list(self, request):
           header = request.META.get('HTTP_ACCEPT', '*/*')
           header = request.query_params.get('_accept', header)
           return [token.strip() for token in header.split(',')]

## Doesn't HTML5 support PUT and DELETE forms?

Nope.  It was at one point intended to support `PUT` and `DELETE` forms, but
was later [dropped from the spec][html5].  There remains
[ongoing discussion][put_delete] about adding support for `PUT` and `DELETE`,
as well as how to support content types other than form-encoded data.

[cite]: https://www.amazon.com/RESTful-Web-Services-Leonard-Richardson/dp/0596529260
[ajax-form]: https://github.com/tomchristie/ajax-form
[rails]: https://guides.rubyonrails.org/form_helpers.html#how-do-forms-with-put-or-delete-methods-work
[html5]: https://www.w3.org/TR/html5-diff/#changes-2010-06-24
[put_delete]: http://amundsen.com/examples/put-delete-forms/
