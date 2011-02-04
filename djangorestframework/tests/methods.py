from django.test import TestCase
from djangorestframework.tests.utils import RequestFactory
from djangorestframework.methods import MethodMixin, StandardMethodMixin, OverloadedPOSTMethodMixin


class TestMethodMixins(TestCase): 
    def setUp(self):
        self.req = RequestFactory()

    # Interface tests

    def test_method_mixin_interface(self):
        """Ensure the base ContentMixin interface is as expected."""
        self.assertRaises(NotImplementedError, MethodMixin().determine_method, None)

    def test_standard_method_mixin_interface(self):
        """Ensure the StandardMethodMixin interface is as expected."""
        self.assertTrue(issubclass(StandardMethodMixin, MethodMixin))
        getattr(StandardMethodMixin, 'determine_method')

    def test_overloaded_method_mixin_interface(self):
        """Ensure the OverloadedPOSTMethodMixin interface is as expected."""
        self.assertTrue(issubclass(OverloadedPOSTMethodMixin, MethodMixin))
        getattr(OverloadedPOSTMethodMixin, 'FORM_PARAM_METHOD')
        getattr(OverloadedPOSTMethodMixin, 'determine_method')

    # Behavioural tests

    def test_standard_behaviour_determines_GET(self):
        """GET requests identified as GET method with StandardMethodMixin"""
        request = self.req.get('/')
        self.assertEqual(StandardMethodMixin().determine_method(request), 'GET')

    def test_standard_behaviour_determines_POST(self):
        """POST requests identified as POST method with StandardMethodMixin"""
        request = self.req.post('/')
        self.assertEqual(StandardMethodMixin().determine_method(request), 'POST')
    
    def test_overloaded_POST_behaviour_determines_GET(self):
        """GET requests identified as GET method with OverloadedPOSTMethodMixin"""
        request = self.req.get('/')
        self.assertEqual(OverloadedPOSTMethodMixin().determine_method(request), 'GET')

    def test_overloaded_POST_behaviour_determines_POST(self):
        """POST requests identified as POST method with OverloadedPOSTMethodMixin"""
        request = self.req.post('/')
        self.assertEqual(OverloadedPOSTMethodMixin().determine_method(request), 'POST')
    
    def test_overloaded_POST_behaviour_determines_overloaded_method(self):
        """POST requests can be overloaded to another method by setting a reserved form field with OverloadedPOSTMethodMixin"""
        request = self.req.post('/', {OverloadedPOSTMethodMixin.FORM_PARAM_METHOD: 'DELETE'})
        self.assertEqual(OverloadedPOSTMethodMixin().determine_method(request), 'DELETE')
