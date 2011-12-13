# Right now we expect this test to fail - I'm just going to leave it commented out.
# Looking forward to actually being able to raise ExpectedFailure sometime!
#
#from django.test import TestCase
#from djangorestframework.response import Response
#
#
#class TestResponse(TestCase):
#
#    # Interface tests
#
#    # This is mainly to remind myself that the Response interface needs to change slightly
#    def test_response_interface(self):
#        """Ensure the Response interface is as expected."""
#        response = Response()
#        getattr(response, 'status')
#        getattr(response, 'content')
#        getattr(response, 'headers')

