from djangorestframework.views import View
from djangorestframework.response import Response


class ProxyView(View):
    """
    A view that just acts as a proxy to call non-djangorestframework views, while still
    displaying the browsable API interface.
    """

    view_class = None

    def dispatch(self, request, *args, **kwargs):
        self.request = request = self.create_request(request)
        if request.method in ['PUT', 'POST']:
            self.response = self.view_class.as_view()(request, *args, **kwargs)
        return super(ProxyView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return Response()

    def put(self, request, *args, **kwargs):
        return Response(self.response.content)

    def post(self, request, *args, **kwargs):
        return Response(self.response.content)

    def get_name(self):    
        return self.view_class.__name__

    def get_description(self, html):
        return self.view_class.__doc__
