from django.test import TestCase
from djangorestframework.compat import RequestFactory
from djangorestframework.mixins import RequestMixin


class TestMethodOverloading(TestCase):
    def setUp(self):
        self.req = RequestFactory()

    def test_standard_behaviour_determines_GET(self):
        """GET requests identified"""
        view = RequestMixin()
        view.request = self.req.get('/')
        self.assertEqual(view.method, 'GET')

    def test_standard_behaviour_determines_POST(self):
        """POST requests identified"""
        view = RequestMixin()
        view.request = self.req.post('/')
        self.assertEqual(view.method, 'POST')

    def test_overloaded_POST_behaviour_determines_overloaded_method(self):
        """POST requests can be overloaded to another method by setting a reserved form field"""
        view = RequestMixin()
        view.request = self.req.post('/', {view._METHOD_PARAM: 'DELETE'})
        self.assertEqual(view.method, 'DELETE')

    def test_HEAD_is_a_valid_method(self):
        """HEAD requests identified"""
        view = RequestMixin()
        view.request = self.req.head('/')
        self.assertEqual(view.method, 'HEAD')
