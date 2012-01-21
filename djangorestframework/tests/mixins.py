"""Tests for the mixin module"""
from django import forms
from django.core.exceptions import ValidationError
from django.conf.urls.defaults import patterns, url
from django.test import TestCase
from django.utils import simplejson as json
from djangorestframework import status
from djangorestframework.compat import RequestFactory
from django.contrib.auth.models import Group, User
from djangorestframework.mixins import CreateModelMixin, PaginatorMixin, RequestFormMixin
from djangorestframework.resources import ModelResource
from djangorestframework.response import Response, ErrorResponse
from djangorestframework.tests.models import CustomUser
from djangorestframework.tests.testcases import TestModelsTestCase
from djangorestframework.views import View


class TestModelCreation(TestModelsTestCase):
    """Tests on CreateModelMixin"""

    def setUp(self):
        super(TestModelsTestCase, self).setUp()
        self.req = RequestFactory()

    def test_creation(self):
        self.assertEquals(0, Group.objects.count())

        class GroupResource(ModelResource):
            model = Group

        form_data = {'name': 'foo'}
        request = self.req.post('/groups', data=form_data)
        mixin = CreateModelMixin()
        mixin.resource = GroupResource
        mixin.CONTENT = form_data

        response = mixin.post(request)
        self.assertEquals(1, Group.objects.count())
        self.assertEquals('foo', response.cleaned_content.name)

    def test_creation_with_m2m_relation(self):
        class UserResource(ModelResource):
            model = User

            def url(self, instance):
                return "/users/%i" % instance.id

        group = Group(name='foo')
        group.save()

        form_data = {
            'username': 'bar',
            'password': 'baz',
            'groups': [group.id]
        }
        request = self.req.post('/groups', data=form_data)
        cleaned_data = dict(form_data)
        cleaned_data['groups'] = [group]
        mixin = CreateModelMixin()
        mixin.resource = UserResource
        mixin.CONTENT = cleaned_data

        response = mixin.post(request)
        self.assertEquals(1, User.objects.count())
        self.assertEquals(1, response.cleaned_content.groups.count())
        self.assertEquals('foo', response.cleaned_content.groups.all()[0].name)

    def test_creation_with_m2m_relation_through(self):
        """
        Tests creation where the m2m relation uses a through table
        """
        class UserResource(ModelResource):
            model = CustomUser

            def url(self, instance):
                return "/customusers/%i" % instance.id

        form_data = {'username': 'bar0', 'groups': []}
        request = self.req.post('/groups', data=form_data)
        cleaned_data = dict(form_data)
        cleaned_data['groups'] = []
        mixin = CreateModelMixin()
        mixin.resource = UserResource
        mixin.CONTENT = cleaned_data

        response = mixin.post(request)
        self.assertEquals(1, CustomUser.objects.count())
        self.assertEquals(0, response.cleaned_content.groups.count())

        group = Group(name='foo1')
        group.save()

        form_data = {'username': 'bar1', 'groups': [group.id]}
        request = self.req.post('/groups', data=form_data)
        cleaned_data = dict(form_data)
        cleaned_data['groups'] = [group]
        mixin = CreateModelMixin()
        mixin.resource = UserResource
        mixin.CONTENT = cleaned_data

        response = mixin.post(request)
        self.assertEquals(2, CustomUser.objects.count())
        self.assertEquals(1, response.cleaned_content.groups.count())
        self.assertEquals('foo1', response.cleaned_content.groups.all()[0].name)

        group2 = Group(name='foo2')
        group2.save()

        form_data = {'username': 'bar2', 'groups': [group.id, group2.id]}
        request = self.req.post('/groups', data=form_data)
        cleaned_data = dict(form_data)
        cleaned_data['groups'] = [group, group2]
        mixin = CreateModelMixin()
        mixin.resource = UserResource
        mixin.CONTENT = cleaned_data

        response = mixin.post(request)
        self.assertEquals(3, CustomUser.objects.count())
        self.assertEquals(2, response.cleaned_content.groups.count())
        self.assertEquals('foo1', response.cleaned_content.groups.all()[0].name)
        self.assertEquals('foo2', response.cleaned_content.groups.all()[1].name)


class MockPaginatorView(PaginatorMixin, View):
    total = 60

    def get(self, request):
        return range(0, self.total)

    def post(self, request):
        return Response(status.HTTP_201_CREATED, {'status': 'OK'})


class TestPagination(TestCase):
    def setUp(self):
        self.req = RequestFactory()

    def test_default_limit(self):
        """ Tests if pagination works without overwriting the limit """
        request = self.req.get('/paginator')
        response = MockPaginatorView.as_view()(request)

        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(MockPaginatorView.total, content['total'])
        self.assertEqual(MockPaginatorView.limit, content['per_page'])

        self.assertEqual(range(0, MockPaginatorView.limit), content['results'])

    def test_overwriting_limit(self):
        """ Tests if the limit can be overwritten """
        limit = 10

        request = self.req.get('/paginator')
        response = MockPaginatorView.as_view(limit=limit)(request)

        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
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

        self.assertEqual(response.status_code, status.HTTP_200_OK)
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

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(MockPaginatorView.total, content['total'])
        self.assertNotEqual(limit, content['per_page'])
        self.assertNotEqual(num_pages, content['pages'])
        self.assertEqual(MockPaginatorView.limit, content['per_page'])

    def test_only_works_for_get(self):
        """ Pagination should only work for GET requests """
        request = self.req.post('/paginator', data={'content': 'spam'})
        response = MockPaginatorView.as_view()(request)

        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(None, content.get('per_page'))
        self.assertEqual('OK', content['status'])

    def test_non_int_page(self):
        """ Tests that it can handle invalid values """
        request = self.req.get('/paginator/?page=spam')
        response = MockPaginatorView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_page_range(self):
        """ Tests that the page range is handle correctly """
        request = self.req.get('/paginator/?page=0')
        response = MockPaginatorView.as_view()(request)
        content = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        request = self.req.get('/paginator/')
        response = MockPaginatorView.as_view()(request)
        content = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(range(0, MockPaginatorView.limit), content['results'])

        num_pages = content['pages']

        request = self.req.get('/paginator/?page=%d' % num_pages)
        response = MockPaginatorView.as_view()(request)
        content = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(range(MockPaginatorView.limit*(num_pages-1), MockPaginatorView.total), content['results'])

        request = self.req.get('/paginator/?page=%d' % (num_pages + 1,))
        response = MockPaginatorView.as_view()(request)
        content = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_existing_query_parameters_are_preserved(self):
        """ Tests that existing query parameters are preserved when
        generating next/previous page links """
        request = self.req.get('/paginator/?foo=bar&another=something')
        response = MockPaginatorView.as_view()(request)
        content = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('foo=bar' in content['next'])
        self.assertTrue('another=something' in content['next'])
        self.assertTrue('page=2' in content['next'])


class RequestFormMockView(View):
    """This is a request form mock view"""

    class MockForm(forms.Form, RequestFormMixin):
        foo = forms.BooleanField(required=False)
        bar = forms.IntegerField(help_text='Must be an integer.')
        baz = forms.CharField(max_length=32)

    def clean(self):
        if not hasattr(self, "request"):
            raise ValidationError("Request Not Set")
        return super(MockForm, self).clean()

    form = MockForm


urlpatterns = patterns('',
    url(r'^requestformmock/$', RequestFormMockView.as_view()),
)

class TestRequestFormMixin(TestCase):
    """Tests the RequestFormMixin"""
    urls = 'djangorestframework.tests.mixins'

    def test_options_method_simple_view(self):
        response = self.client.options('/requestformmock/')
        self.assertEqual(response.status_code, status.OK)

