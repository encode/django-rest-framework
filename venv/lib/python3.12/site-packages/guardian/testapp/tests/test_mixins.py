from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ImproperlyConfigured
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import TestCase
from django.test.client import RequestFactory
from django.views.generic import View
from django.views.generic import ListView

from guardian.shortcuts import assign_perm
from unittest import mock
from guardian.mixins import LoginRequiredMixin
from guardian.mixins import PermissionRequiredMixin
from guardian.mixins import PermissionListMixin

from ..models import Post


class DatabaseRemovedError(Exception):
    pass


class RemoveDatabaseView(View):

    def get(self, request, *args, **kwargs):
        raise DatabaseRemovedError("You've just allowed db to be removed!")


class TestView(PermissionRequiredMixin, RemoveDatabaseView):
    permission_required = 'testapp.change_post'
    object = None  # should be set at each tests explicitly


class NoObjectView(PermissionRequiredMixin, RemoveDatabaseView):
    permission_required = 'testapp.change_post'


class GlobalNoObjectView(PermissionRequiredMixin, RemoveDatabaseView):
    permission_required = 'testapp.add_post'
    accept_global_perms = True


class PostPermissionListView(PermissionListMixin, ListView):
    model = Post
    permission_required = 'testapp.change_post'
    template_name = 'list.html'


class TestViewMixins(TestCase):

    def setUp(self):
        self.post = Post.objects.create(title='foo-post-title')
        self.factory = RequestFactory()
        self.user = get_user_model().objects.create_user(
            'joe', 'joe@doe.com', 'doe')
        self.client.login(username='joe', password='doe')

    def test_permission_is_checked_before_view_is_computed(self):
        """
        This test would fail if permission is checked **after** view is
        actually resolved.
        """
        request = self.factory.get('/')
        request.user = self.user
        # View.object is set
        view = TestView.as_view(object=self.post)
        response = view(request)
        self.assertEqual(response.status_code, 302)

        # View.get_object returns object
        TestView.get_object = lambda instance: self.post
        view = TestView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 302)
        del TestView.get_object

    def test_permission_is_checked_before_view_is_computed_perm_denied_raised(self):
        """
        This test would fail if permission is checked **after** view is
        actually resolved.
        """
        request = self.factory.get('/')
        request.user = self.user
        view = TestView.as_view(raise_exception=True, object=self.post)
        with self.assertRaises(PermissionDenied):
            view(request)

    def test_permission_required_view_configured_wrongly(self):
        """
        This test would fail if permission is checked **after** view is
        actually resolved.
        """
        request = self.factory.get('/')
        request.user = self.user
        request.user.add_obj_perm('change_post', self.post)
        view = TestView.as_view(permission_required=None, object=self.post)
        with self.assertRaises(ImproperlyConfigured):
            view(request)

    def test_permission_required(self):
        """
        This test would fail if permission is checked **after** view is
        actually resolved.
        """
        request = self.factory.get('/')
        request.user = self.user
        request.user.add_obj_perm('change_post', self.post)
        view = TestView.as_view(object=self.post)
        with self.assertRaises(DatabaseRemovedError):
            view(request)

    def test_permission_required_no_object(self):
        """
        This test would fail if permission is checked on a view's
        object when it has none
        """

        request = self.factory.get('/')
        request.user = self.user
        request.user.add_obj_perm('change_post', self.post)
        view = NoObjectView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 302)

    def test_permission_required_global_no_object(self):
        """
        This test would fail if permission is checked on a view's
        object when it not set and **no** global permission
        """

        request = self.factory.get('/')
        request.user = self.user
        view = GlobalNoObjectView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 302)

    def test_permission_granted_global_no_object(self):
        """
        This test would fail if permission is checked on a view's
        object when it not set and **has** global permission
        """

        request = self.factory.get('/')
        request.user = self.user
        assign_perm('testapp.add_post', request.user)
        view = GlobalNoObjectView.as_view()
        with self.assertRaises(DatabaseRemovedError):
            view(request)

    def test_permission_required_as_list(self):
        """
        This test would fail if permission is checked **after** view is
        actually resolved.
        """

        global TestView

        class SecretView(TestView):
            on_permission_check_fail = mock.Mock()

        request = self.factory.get('/')
        request.user = self.user
        request.user.add_obj_perm('change_post', self.post)
        SecretView.permission_required = ['testapp.change_post',
                                          'testapp.add_post']
        view = SecretView.as_view(object=self.post)
        response = view(request)
        self.assertEqual(response.status_code, 302)
        SecretView.on_permission_check_fail.assert_called_once_with(request,
                                                                    response, obj=self.post)

        request.user.add_obj_perm('add_post', self.post)
        with self.assertRaises(DatabaseRemovedError):
            view(request)

    def test_login_required_mixin(self):

        class SecretView(LoginRequiredMixin, View):
            redirect_field_name = 'foobar'
            login_url = '/let-me-in/'

            def get(self, request):
                return HttpResponse('secret-view')

        request = self.factory.get('/some-secret-page/')
        request.user = AnonymousUser()

        view = SecretView.as_view()

        response = view(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'],
                         '/let-me-in/?foobar=/some-secret-page/')

        request.user = self.user
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'secret-view')

    def test_list_permission(self):
        request = self.factory.get('/some-secret-list/')
        request.user = AnonymousUser()

        view = PostPermissionListView.as_view()

        response = view(request)
        self.assertNotContains(response, b'foo-post-title')

        request.user = self.user
        request.user.add_obj_perm('change_post', self.post)

        response = view(request)
        self.assertContains(response, b'foo-post-title')

    def test_any_perm_parameter(self):
        request = self.factory.get('/')
        request.user = self.user
        request.user.add_obj_perm('view_post', self.post)
        self.assertIs(request.user.has_perm('view_post', self.post), True)
        self.assertIs(request.user.has_perm('change_post', self.post), False)
        # success way
        view = TestView.as_view(
            any_perm=True,
            permission_required=['change_post', 'view_post'],
            object=self.post,
        )
        with self.assertRaises(DatabaseRemovedError):
            view(request)
        # fail way
        view = TestView.as_view(
            any_perm=False,
            permission_required=['change_post', 'view_post'],
            object=self.post,
        )
        response = view(request)
        self.assertEqual(response.status_code, 302)
