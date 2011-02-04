from django.test import TestCase
from djangorestframework.response import Response

try:
    import unittest2
except:
    unittest2 = None
else:
    import warnings
    warnings.filterwarnings("ignore")

if unittest2:
    class TestResponse(TestCase, unittest2.TestCase): 
    
        # Interface tests
    
        # This is mainly to remind myself that the Response interface needs to change slightly
        @unittest2.expectedFailure
        def test_response_interface(self):
            """Ensure the Response interface is as expected."""
            response = Response()
            getattr(response, 'status')
            getattr(response, 'content')
            getattr(response, 'headers')

