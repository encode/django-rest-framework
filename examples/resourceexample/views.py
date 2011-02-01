from django import forms
from djangorestframework.resource import Resource
from djangorestframework.response import Response, status


class MyForm(forms.Form):
    foo = forms.BooleanField()
    bar = forms.IntegerField(help_text='Must be an integer.')
    baz = forms.CharField(max_length=32, help_text='Free text.  Max length 32 chars.')


class ExampleResource(Resource):
    """A basic read only resource that points to 3 other resources."""
    allowed_methods = anon_allowed_methods = ('GET',)

    def get(self, request, auth):
        return {"Some other resources": [self.reverse(AnotherExampleResource, num=num) for num in range(3)]}


class AnotherExampleResource(Resource):
    """A basic GET-able/POST-able resource."""
    allowed_methods = anon_allowed_methods = ('GET', 'POST')
    form = MyForm   # Optional form validation on input

    def get(self, request, auth, num):
        """Handle GET requests"""
        if int(num) > 2:
            return Response(status.HTTP_404_NOT_FOUND)
        return "GET request to AnotherExampleResource %s" % num
    
    def post(self, request, auth, content, num):
        """Handle POST requests"""
        if int(num) > 2:
            return Response(status.HTTP_404_NOT_FOUND)
        return "POST request to AnotherExampleResource %s, with content: %s" % (num, repr(content))
