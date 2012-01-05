"""Tests for the mixin module"""
from django.test import TestCase
from django.utils import simplejson as json
from djangorestframework import status
from djangorestframework.compat import RequestFactory
from django.contrib.auth.models import Group, User
from djangorestframework.mixins import PaginatorMixin
from djangorestframework.response import Response
from djangorestframework.tests.testcases import TestModelsTestCase
from djangorestframework.views import View


class MockPaginatorView(PaginatorMixin, View):
    total = 60

    def get(self, request):
        return range(0, self.total)

    def post(self, request):
        return Response(status.CREATED, {'status': 'OK'})


class TestPagination(TestCase):
    def setUp(self):
        self.req = RequestFactory()

    def test_default_limit(self):
        """ Tests if pagination works without overwriting the limit """
        request = self.req.get('/paginator')
        response = MockPaginatorView.as_view()(request)

        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.OK)
        self.assertEqual(MockPaginatorView.total, content['total'])
        self.assertEqual(MockPaginatorView.limit, content['per_page'])

        self.assertEqual(range(0, MockPaginatorView.limit), content['results'])

    def test_overwriting_limit(self):
        """ Tests if the limit can be overwritten """
        limit = 10

        request = self.req.get('/paginator')
        response = MockPaginatorView.as_view(limit=limit)(request)

        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.OK)
        self.assertEqual(content['per_page'], limit)

        self.assertEqual(range(0, limit), content['results'])

    def test_limit_param(self):
        """ Tests if the client can set the limit """
        from math import ceil

        limit = 5
        num_pages = int(ceil(MockPaginatorView.total / float(limit)))

        request = self.req.get('/paginator/?limit=%d' % limit)
        response = MockPaginatorView.as_view()(request)

        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.OK)
        self.assertEqual(MockPaginatorView.total, content['total'])
        self.assertEqual(limit, content['per_page'])
        self.assertEqual(num_pages, content['pages'])

    def test_exceeding_limit(self):
        """ Makes sure the client cannot exceed the default limit """
        from math import ceil

        limit = MockPaginatorView.limit + 10
        num_pages = int(ceil(MockPaginatorView.total / float(limit)))

        request = self.req.get('/paginator/?limit=%d' % limit)
        response = MockPaginatorView.as_view()(request)

        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.OK)
        self.assertEqual(MockPaginatorView.total, content['total'])
        self.assertNotEqual(limit, content['per_page'])
        self.assertNotEqual(num_pages, content['pages'])
        self.assertEqual(MockPaginatorView.limit, content['per_page'])

    def test_only_works_for_get(self):
        """ Pagination should only work for GET requests """
        request = self.req.post('/paginator', data={'content': 'spam'})
        response = MockPaginatorView.as_view()(request)

        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.CREATED)
        self.assertEqual(None, content.get('per_page'))
        self.assertEqual('OK', content['status'])

    def test_non_int_page(self):
        """ Tests that it can handle invalid values """
        request = self.req.get('/paginator/?page=spam')
        response = MockPaginatorView.as_view()(request)

        self.assertEqual(response.status_code, status.NOT_FOUND)

    def test_page_range(self):
        """ Tests that the page range is handle correctly """
        request = self.req.get('/paginator/?page=0')
        response = MockPaginatorView.as_view()(request)
        content = json.loads(response.content)
        self.assertEqual(response.status_code, status.NOT_FOUND)

        request = self.req.get('/paginator/')
        response = MockPaginatorView.as_view()(request)
        content = json.loads(response.content)
        self.assertEqual(response.status_code, status.OK)
        self.assertEqual(range(0, MockPaginatorView.limit), content['results'])

        num_pages = content['pages']

        request = self.req.get('/paginator/?page=%d' % num_pages)
        response = MockPaginatorView.as_view()(request)
        content = json.loads(response.content)
        self.assertEqual(response.status_code, status.OK)
        self.assertEqual(range(MockPaginatorView.limit*(num_pages-1), MockPaginatorView.total), content['results'])

        request = self.req.get('/paginator/?page=%d' % (num_pages + 1,))
        response = MockPaginatorView.as_view()(request)
        content = json.loads(response.content)
        self.assertEqual(response.status_code, status.NOT_FOUND)
