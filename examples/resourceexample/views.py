from django.core.urlresolvers import reverse

from djangorestframework.resource import Resource
from djangorestframework.response import Response
from djangorestframework import status

from resourceexample.forms import MyForm

class ExampleResource(Resource):
    """A basic read-only resource that points to 3 other resources."""

    def get(self, request):
        return {"Some other resources": [reverse('another-example-resource', kwargs={'num':num}) for num in range(3)]}

class AnotherExampleResource(Resource):
    """A basic GET-able/POST-able resource."""
    form = MyForm # Optional form validation on input (Applies in this case the POST method, but can also apply to PUT)

    def get(self, request, num):
        """Handle GET requests"""
        if int(num) > 2:
            return Response(status.HTTP_404_NOT_FOUND)
        return "GET request to AnotherExampleResource %s" % num
    
    def post(self, request, num):
        """Handle POST requests"""
        if int(num) > 2:
            return Response(status.HTTP_404_NOT_FOUND)
        return "POST request to AnotherExampleResource %s, with content: %s" % (num, repr(self.CONTENT))
