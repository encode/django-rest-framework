from djangorestframework.compat import View
from django.http import HttpResponse
from django.core.urlresolvers import reverse

from djangorestframework.mixins import RequestMixin
from djangorestframework.views import View as DRFView
from djangorestframework import parsers
from djangorestframework.response import Response


class RequestExampleView(DRFView):
    """
    A container view for request examples.
    """

    def get(self, request):
        return Response([{'name': 'request.DATA Example', 'url': reverse('request-content')},])


class MyBaseViewUsingEnhancedRequest(RequestMixin, View):
    """
    Base view enabling the usage of enhanced requests with user defined views.
    """

    parser_classes = parsers.DEFAULT_PARSERS

    def dispatch(self, request, *args, **kwargs):
        self.request = request = self.create_request(request)
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

