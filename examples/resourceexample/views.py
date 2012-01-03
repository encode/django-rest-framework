from django.core.urlresolvers import reverse

from djangorestframework.views import View
from djangorestframework.response import Response
from djangorestframework import status

from resourceexample.forms import MyForm


class ExampleView(View):
    """
    A basic read-only view that points to 3 other views.
    """

    def get(self, request):
        """
        Handle GET requests, returning a list of URLs pointing to 3 other views.
        """
        return {"Some other resources": [reverse('another-example', kwargs={'num':num}) for num in range(3)]}


class AnotherExampleView(View):
    """
    A basic view, that can be handle GET and POST requests.
    Applies some simple form validation on POST requests.
    """
    form = MyForm

    def get(self, request, num):
        """
        Handle GET requests.
        Returns a simple string indicating which view the GET request was for.
        """
        if int(num) > 2:
            return Response(status.HTTP_404_NOT_FOUND)
        return "GET request to AnotherExampleResource %s" % num

    def post(self, request, num):
        """
        Handle POST requests, with form validation.
        Returns a simple string indicating what content was supplied.
        """
        if int(num) > 2:
            return Response(status.HTTP_404_NOT_FOUND)
        return "POST request to AnotherExampleResource %s, with content: %s" % (num, repr(self.CONTENT))
