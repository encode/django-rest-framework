from django.core.urlresolvers import reverse

from djangorestframework.views import BaseView
from djangorestframework.resources import FormResource
from djangorestframework.response import Response
from djangorestframework import status

from resourceexample.forms import MyForm

class MyFormValidation(FormResource):
    """
    A resource which applies form validation on the input.
    """
    form = MyForm

    
class ExampleResource(BaseView):
    """
    A basic read-only resource that points to 3 other resources.
    """

    def get(self, request):
        return {"Some other resources": [reverse('another-example-resource', kwargs={'num':num}) for num in range(3)]}


class AnotherExampleResource(BaseView):
    """
    A basic GET-able/POST-able resource.
    """
    resource = MyFormValidation

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
