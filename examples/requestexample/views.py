from djangorestframework.compat import View
from django.http import HttpResponse
from django.core.urlresolvers import reverse

from djangorestframework.mixins import RequestMixin
from djangorestframework.views import View as DRFView
from djangorestframework import parsers


class RequestExampleView(DRFView):
    """
    A container view for request examples.
    """

    def get(self, request):
        return [{'name': 'request.DATA Example', 'url': reverse('request-content')},]


class MyBaseViewUsingEnhancedRequest(RequestMixin, View):
    """
    Base view enabling the usage of enhanced requests with user defined views.
    """

    parsers = parsers.DEFAULT_PARSERS

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        request = self.get_request()
        return super(MyBaseViewUsingEnhancedRequest, self).dispatch(request, *args, **kwargs)


class EchoRequestContentView(MyBaseViewUsingEnhancedRequest):
    """
    A view that just reads the items in `request.DATA` and echoes them back.
    """

    def post(self, request, *args, **kwargs):
        return HttpResponse(("Found %s in request.DATA, content : %s" %
            (type(request.DATA), request.DATA)))

    def put(self, request, *args, **kwargs):
        return HttpResponse(("Found %s in request.DATA, content : %s" %
            (type(request.DATA), request.DATA)))


class MockView(DRFView):
    """
    A view that just acts as a proxy to call non-djangorestframework views, while still
    displaying the browsable API interface.
    """

    view_class = None

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        if self.get_request().method in ['PUT', 'POST']:
            self.response = self.view_class.as_view()(request, *args, **kwargs)
        return super(MockView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return

    def put(self, request, *args, **kwargs):
        return self.response.content

    def post(self, request, *args, **kwargs):
        return self.response.content

    def __getattribute__(self, name):
        if name == '__name__':
            return self.view_class.__name__
        elif name == '__doc__':
            return self.view_class.__doc__
        else:
            return super(MockView, self).__getattribute__(name)

