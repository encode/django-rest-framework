import django
from django.conf import global_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, AnonymousUser
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db.models.base import ModelBase
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.http import HttpResponseNotFound
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template import TemplateDoesNotExist
from django.test import TestCase

from guardian.compat import get_user_model_path
from guardian.compat import get_user_permission_full_codename
from unittest import mock
from guardian.decorators import permission_required, permission_required_or_403, permission_required_or_404
from guardian.exceptions import GuardianError
from guardian.exceptions import WrongAppError
from guardian.shortcuts import assign_perm
from guardian.testapp.tests.conf import TestDataMixin
from guardian.testapp.tests.conf import override_settings
from guardian.testapp.tests.conf import skipUnlessTestApp

User = get_user_model()
user_model_path = get_user_model_path()


@skipUnlessTestApp
class PermissionRequiredTest(TestDataMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.anon = AnonymousUser()
        self.user = User.objects.get_or_create(username='jack')[0]
        self.group = Group.objects.get_or_create(name='jackGroup')[0]

    def _get_request(self, user=None):
        if user is None:
            user = AnonymousUser()
        request = HttpRequest()
        request.user = user
        return request

    def test_no_args(self):

        try:
            @permission_required
            def dummy_view(request):
                return HttpResponse('dummy_view')
        except GuardianError:
            pass
        else:
            self.fail("Trying to decorate using permission_required without "
                      "permission as first argument should raise exception")

    def test_RENDER_403_is_false(self):
        request = self._get_request(self.anon)

        @permission_required_or_403('not_installed_app.change_user')
        def dummy_view(request):
            return HttpResponse('dummy_view')

        with mock.patch('guardian.conf.settings.RENDER_403', False):
            response = dummy_view(request)
            self.assertEqual(response.content, b'')
            self.assertTrue(isinstance(response, HttpResponseForbidden))

    def test_RENDER_404_is_false(self):
        request = self._get_request(self.anon)

        @permission_required_or_404('not_installed_app.change_user')
        def dummy_view(request):
            return HttpResponse('dummy_view')

        with mock.patch('guardian.conf.settings.RENDER_404', False):
            response = dummy_view(request)
            self.assertEqual(response.content, b'')
            self.assertTrue(isinstance(response, HttpResponseNotFound))

    @mock.patch('guardian.conf.settings.RENDER_403', True)
    def test_TEMPLATE_403_setting(self):
        request = self._get_request(self.anon)

        @permission_required_or_403('not_installed_app.change_user')
        def dummy_view(request):
            return HttpResponse('dummy_view')

        with mock.patch('guardian.conf.settings.TEMPLATE_403', 'dummy403.html'):
            response = dummy_view(request)
            self.assertEqual(response.content, b'foobar403\n')

    @mock.patch('guardian.conf.settings.RENDER_404', True)
    def test_TEMPLATE_404_setting(self):
        request = self._get_request(self.anon)

        @permission_required_or_404('not_installed_app.change_user')
        def dummy_view(request):
            return HttpResponse('dummy_view')

        with mock.patch('guardian.conf.settings.TEMPLATE_404', 'dummy404.html'):
            response = dummy_view(request)
            self.assertEqual(response.content, b'foobar404\n')

    @mock.patch('guardian.conf.settings.RENDER_403', True)
    def test_403_response_raises_error(self):
        request = self._get_request(self.anon)

        @permission_required_or_403('not_installed_app.change_user')
        def dummy_view(request):
            return HttpResponse('dummy_view')
        with mock.patch('guardian.conf.settings.TEMPLATE_403',
                        '_non-exisitng-403.html'):
            self.assertRaises(TemplateDoesNotExist, dummy_view, request)

    @mock.patch('guardian.conf.settings.RENDER_404', True)
    def test_404_response_raises_error(self):
        request = self._get_request(self.anon)

        @permission_required_or_404('not_installed_app.change_user')
        def dummy_view(request):
            return HttpResponse('dummy_view')
        with mock.patch('guardian.conf.settings.TEMPLATE_404',
                        '_non-exisitng-404.html'):
            self.assertRaises(TemplateDoesNotExist, dummy_view, request)

    @mock.patch('guardian.conf.settings.RENDER_403', False)
    @mock.patch('guardian.conf.settings.RAISE_403', True)
    def test_RAISE_403_setting_is_true(self):
        request = self._get_request(self.anon)

        @permission_required_or_403('not_installed_app.change_user')
        def dummy_view(request):
            return HttpResponse('dummy_view')

        self.assertRaises(PermissionDenied, dummy_view, request)

    @mock.patch('guardian.conf.settings.RENDER_404', False)
    @mock.patch('guardian.conf.settings.RAISE_404', True)
    def test_RAISE_404_setting_is_true(self):
        request = self._get_request(self.anon)

        @permission_required_or_404('not_installed_app.change_user')
        def dummy_view(request):
            return HttpResponse('dummy_view')

        self.assertRaises(ObjectDoesNotExist, dummy_view, request)

    def test_anonymous_user_wrong_app(self):

        request = self._get_request(self.anon)

        @permission_required_or_403('not_installed_app.change_user')
        def dummy_view(request):
            return HttpResponse('dummy_view')
        self.assertEqual(dummy_view(request).status_code, 403)

    def test_anonymous_user_wrong_codename(self):

        request = self._get_request()

        @permission_required_or_403('auth.wrong_codename')
        def dummy_view(request):
            return HttpResponse('dummy_view')
        self.assertEqual(dummy_view(request).status_code, 403)

    def test_anonymous_user(self):

        request = self._get_request()

        @permission_required_or_403('auth.change_user')
        def dummy_view(request):
            return HttpResponse('dummy_view')
        self.assertEqual(dummy_view(request).status_code, 403)

    def test_wrong_lookup_variables_number(self):

        request = self._get_request()

        try:
            @permission_required_or_403('auth.change_user', (User, 'username'))
            def dummy_view(request, username):
                pass
            dummy_view(request, username='jack')
        except GuardianError:
            pass
        else:
            self.fail("If lookup variables are passed they must be tuple of: "
                      "(ModelClass/app_label.ModelClass/queryset, "
                      "<pair of lookup_string and view_arg>)\n"
                      "Otherwise GuardianError should be raised")

    def test_wrong_lookup_variables(self):

        request = self._get_request()

        args = (
            (2010, 'username', 'username'),
            ('User', 'username', 'username'),
            (User, 'username', 'no_arg'),
        )
        for tup in args:
            try:
                @permission_required_or_403('auth.change_user', tup)
                def show_user(request, username):
                    user = get_object_or_404(User, username=username)
                    return HttpResponse("It's %s here!" % user.username)
                show_user(request, 'jack')
            except GuardianError:
                pass
            else:
                self.fail("Wrong arguments given but GuardianError not raised")

    def test_user_has_no_access(self):

        request = self._get_request()

        @permission_required_or_403('auth.change_user')
        def dummy_view(request):
            return HttpResponse('dummy_view')
        self.assertEqual(dummy_view(request).status_code, 403)

    def test_user_has_access(self):

        perm = get_user_permission_full_codename('change')
        joe, created = User.objects.get_or_create(username='joe')
        assign_perm(perm, self.user, obj=joe)

        request = self._get_request(self.user)

        @permission_required_or_403(perm, (
            user_model_path, 'username', 'username'))
        def dummy_view(request, username):
            return HttpResponse('dummy_view')
        response = dummy_view(request, username='joe')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'dummy_view')

    def test_user_has_access_on_model_with_metaclass(self):
        """
        Test to the fix issues of comparaison made via type()
        in the decorator. In the case of a `Model` implementing
        a custom metaclass, the decorator fail because type
        doesn't return `ModelBase`
        """
        perm = get_user_permission_full_codename('change')

        class TestMeta(ModelBase):
            pass

        class ProxyUser(User):

            class Meta:
                proxy = True
                app_label = User._meta.app_label
            __metaclass__ = TestMeta

        joe, created = ProxyUser.objects.get_or_create(username='joe')
        assign_perm(perm, self.user, obj=joe)

        request = self._get_request(self.user)

        @permission_required_or_403(perm, (
            ProxyUser, 'username', 'username'))
        def dummy_view(request, username):
            return HttpResponse('dummy_view')
        response = dummy_view(request, username='joe')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'dummy_view')

    def test_user_has_obj_access_even_if_we_also_check_for_global(self):

        perm = get_user_permission_full_codename('change')
        joe, created = User.objects.get_or_create(username='joe')
        assign_perm(perm, self.user, obj=joe)

        request = self._get_request(self.user)

        @permission_required_or_403(perm, (
            user_model_path, 'username', 'username'), accept_global_perms=True)
        def dummy_view(request, username):
            return HttpResponse('dummy_view')
        response = dummy_view(request, username='joe')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'dummy_view')

    def test_user_has_no_obj_perm_access(self):

        perm = get_user_permission_full_codename('change')
        joe, created = User.objects.get_or_create(username='joe')

        request = self._get_request(self.user)

        @permission_required_or_403(perm, (
            user_model_path, 'username', 'username'))
        def dummy_view(request, username):
            return HttpResponse('dummy_view')
        response = dummy_view(request, username='joe')
        self.assertEqual(response.status_code, 403)

    def test_user_has_global_perm_access_but_flag_not_set(self):

        perm = get_user_permission_full_codename('change')
        joe, created = User.objects.get_or_create(username='joe')
        assign_perm(perm, self.user)

        request = self._get_request(self.user)

        @permission_required_or_403(perm, (
            user_model_path, 'username', 'username'))
        def dummy_view(request, username):
            return HttpResponse('dummy_view')
        response = dummy_view(request, username='joe')
        self.assertEqual(response.status_code, 403)

    def test_user_has_global_perm_access(self):

        perm = get_user_permission_full_codename('change')
        joe, created = User.objects.get_or_create(username='joe')
        assign_perm(perm, self.user)

        request = self._get_request(self.user)

        @permission_required_or_403(perm, (
            user_model_path, 'username', 'username'), accept_global_perms=True)
        def dummy_view(request, username):
            return HttpResponse('dummy_view')
        response = dummy_view(request, username='joe')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'dummy_view')

    def test_model_lookup(self):

        request = self._get_request(self.user)

        perm = get_user_permission_full_codename('change')
        joe, created = User.objects.get_or_create(username='joe')
        assign_perm(perm, self.user, obj=joe)

        models = (
            user_model_path,
            User,
            User.objects.filter(is_active=True),
        )
        for model in models:
            @permission_required_or_403(perm, (model, 'username', 'username'))
            def dummy_view(request, username):
                get_object_or_404(User, username=username)
                return HttpResponse('hello')
            response = dummy_view(request, username=joe.username)
            self.assertEqual(response.content, b'hello')

    def test_redirection_raises_wrong_app_error(self):
        from guardian.testapp.models import Project
        request = self._get_request(self.user)

        User.objects.create(username='foo')
        Project.objects.create(name='foobar')

        @permission_required('auth.change_group',
                             (Project, 'name', 'group_name'),
                             login_url='/foobar/')
        def dummy_view(request, project_name):
            pass
        # 'auth.change_group' is wrong permission codename (should be one
        # related with User
        self.assertRaises(WrongAppError, dummy_view,
                          request, group_name='foobar')

    def test_redirection(self):
        from guardian.testapp.models import Project

        request = self._get_request(self.user)

        User.objects.create(username='foo')
        Project.objects.create(name='foobar')

        @permission_required('testapp.change_project',
                             (Project, 'name', 'project_name'),
                             login_url='/foobar/')
        def dummy_view(request, project_name):
            pass
        response = dummy_view(request, project_name='foobar')
        self.assertTrue(isinstance(response, HttpResponseRedirect))
        if django.VERSION >= (3, 2):
            self.assertTrue(response.headers['location'].startswith(
                '/foobar/'))
        else:
            self.assertTrue(response._headers['location'][1].startswith(
                '/foobar/'))

    @override_settings(LOGIN_URL='django.contrib.auth.views.login')
    def test_redirection_class(self):
        view_url = '/permission_required/'

        response = self.client.get(view_url)
        # this should be '/account/login'
        self.assertRedirects(
            response, global_settings.LOGIN_URL + "?next=" + view_url)
