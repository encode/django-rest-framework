Using the enhanced request in all your views
==============================================

This example shows how you can use Django REST framework's enhanced `request` - :class:`request.Request` - in your own views, without having to use the full-blown :class:`views.View` class.

What can it do for you ? Mostly, it will take care of parsing the request's content, and handling equally all HTTP methods ... 

Before
--------

In order to support `JSON` or other serial formats, you might have parsed manually the request's content with something like : ::

    class MyView(View):

        def put(self, request, *args, **kwargs):
            content_type = request.META['CONTENT_TYPE']
            if (content_type == 'application/json'):
                raw_data = request.read()
                parsed_data = json.loads(raw_data)

            # PLUS as many `elif` as formats you wish to support ...

            # then do stuff with your data :
            self.do_stuff(parsed_data['bla'], parsed_data['hoho'])

            # and finally respond something

... and you were unhappy because this looks hackish.

Also, you might have tried uploading files with a PUT request - *and given up* since that's complicated to achieve even with Django 1.3.


After
------

All the dirty `Content-type` checking and content reading and parsing is done for you, and you only need to do the following : ::

    class MyView(MyBaseViewUsingEnhancedRequest):

        def put(self, request, *args, **kwargs):
            self.do_stuff(request.DATA['bla'], request.DATA['hoho'])
            # and finally respond something

So the parsed content is magically available as `.DATA` on the `request` object.

Also, if you uploaded files, they are available as `.FILES`, like with a normal POST request.

.. note:: Note that all the above is also valid for a POST request.


How to add it to your custom views ?
--------------------------------------

Now that you're convinced you need to use the enhanced request object, here is how you can add it to all your custom views : ::

    from django.views.generic.base import View

    from djangorestframework.mixins import RequestMixin
    from djangorestframework import parsers


    class MyBaseViewUsingEnhancedRequest(RequestMixin, View):
        """
        Base view enabling the usage of enhanced requests with user defined views.
        """

        parser_classes = parsers.DEFAULT_PARSERS

        def dispatch(self, request, *args, **kwargs):
            request = self.prepare_request(request)
            return super(MyBaseViewUsingEnhancedRequest, self).dispatch(request, *args, **kwargs)

And then, use this class as a base for all your custom views.

.. note:: you can see this live in the examples. 
