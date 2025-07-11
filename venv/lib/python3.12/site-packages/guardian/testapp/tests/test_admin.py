import copy
import os
import unittest

from django import VERSION as DJANGO_VERSION, forms
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.http import HttpRequest
from django.test import TestCase
from django.test.client import Client
from django.urls import reverse

from guardian.admin import GuardedModelAdmin
from guardian.shortcuts import get_perms
from guardian.shortcuts import get_perms_for_model
from guardian.models import Group
from guardian.testapp.tests.conf import skipUnlessTestApp
from guardian.testapp.models import LogEntryWithGroup as LogEntry

User = get_user_model()


class ContentTypeGuardedAdmin(GuardedModelAdmin):
    pass

try:
    admin.site.unregister(ContentType)
except admin.sites.NotRegistered:
    pass
admin.site.register(ContentType, ContentTypeGuardedAdmin)


class AdminTests(TestCase):

    def setUp(self):
        self.admin = User.objects.create_superuser('admin', 'admin@example.com',
                                                   'admin')
        self.user = User.objects.create_user('joe', 'joe@example.com', 'joe')
        self.group = Group.objects.create(name='group')
        self.client = Client()
        self.obj = ContentType.objects.create(
            model='bar', app_label='fake-for-guardian-tests')
        self.obj_info = self.obj._meta.app_label, self.obj._meta.model_name

    def tearDown(self):
        self.client.logout()

    def _login_superuser(self):
        self.client.login(username='admin', password='admin')

    def test_view_manage_wrong_obj(self):
        self._login_superuser()
        url = reverse('admin:%s_%s_permissions_manage_user' % self.obj_info,
                      kwargs={'object_pk': -10, 'user_id': self.user.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_view(self):
        self._login_superuser()
        url = reverse('admin:%s_%s_permissions' % self.obj_info,
                      args=[self.obj.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object'], self.obj)

    def test_view_manage_wrong_user(self):
        self._login_superuser()
        url = reverse('admin:%s_%s_permissions_manage_user' % self.obj_info,
                      kwargs={'object_pk': self.obj.pk, 'user_id': -10})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_view_manage_user_form(self):
        self._login_superuser()
        url = reverse('admin:%s_%s_permissions' % self.obj_info,
                      args=[self.obj.pk])
        data = {'user': self.user.username, 'submit_manage_user': 'submit'}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        redirect_url = reverse('admin:%s_%s_permissions_manage_user' %
                               self.obj_info, kwargs={'object_pk': self.obj.pk,
                                                      'user_id': self.user.pk})
        self.assertEqual(response.request['PATH_INFO'], redirect_url)

    @unittest.skipIf(DJANGO_VERSION >= (3, 0) and
                     "mysql" in os.environ.get("DATABASE_URL", ""),
                     "Negative ids no longer work in Django 3.0+ with MySQL.")
    def test_view_manage_negative_user_form(self):
        self._login_superuser()
        url = reverse('admin:%s_%s_permissions' % self.obj_info,
                      args=[self.obj.pk])
        self.user = User.objects.create(username='negative_id_user', pk=-2010)
        data = {'user': self.user.username, 'submit_manage_user': 'submit'}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        redirect_url = reverse('admin:%s_%s_permissions_manage_user' %
                               self.obj_info, args=[self.obj.pk, self.user.pk])
        self.assertEqual(response.request['PATH_INFO'], redirect_url)

    def test_view_manage_user_form_wrong_user(self):
        self._login_superuser()
        url = reverse('admin:%s_%s_permissions' % self.obj_info,
                      args=[self.obj.pk])
        data = {'user': 'wrong-user', 'submit_manage_user': 'submit'}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 0)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('user' in response.context['user_form'].errors)

    def test_view_manage_user_form_wrong_field(self):
        self._login_superuser()
        url = reverse('admin:%s_%s_permissions' % self.obj_info,
                      args=[self.obj.pk])
        data = {'user': '<xss>', 'submit_manage_user': 'submit'}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 0)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('user' in response.context['user_form'].errors)

    def test_view_manage_user_form_empty_user(self):
        self._login_superuser()
        url = reverse('admin:%s_%s_permissions' % self.obj_info,
                      args=[self.obj.pk])
        data = {'user': '', 'submit_manage_user': 'submit'}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 0)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('user' in response.context['user_form'].errors)

    def test_view_manage_user_wrong_perms(self):
        self._login_superuser()
        url = reverse('admin:%s_%s_permissions_manage_user' % self.obj_info,
                      args=[self.obj.pk, self.user.pk])
        perms = ['change_user']  # This is not self.obj related permission
        data = {'permissions': perms}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('permissions' in response.context['form'].errors)

    def test_view_manage_user(self):
        self._login_superuser()
        url = reverse('admin:%s_%s_permissions_manage_user' % self.obj_info,
                      args=[self.obj.pk, self.user.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        choices = {c[0] for c in
                       response.context['form'].fields['permissions'].choices}
        self.assertEqual(
            {p.codename for p in get_perms_for_model(self.obj)},
            choices,
        )

        # Add some perms and check if changes were persisted
        perms = ['change_%s' % self.obj_info[
            1], 'delete_%s' % self.obj_info[1]]
        data = {'permissions': perms}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertIn('selected', str(response.context['form']))
        self.assertEqual(
            set(get_perms(self.user, self.obj)),
            set(perms),
        )

        # Remove perm and check if change was persisted
        perms = ['change_%s' % self.obj_info[1]]
        data = {'permissions': perms}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)

        self.assertEqual(
            set(get_perms(self.user, self.obj)),
            set(perms),
        )

    def test_view_manage_group_form(self):
        self._login_superuser()
        url = reverse('admin:%s_%s_permissions' % self.obj_info,
                      args=[self.obj.pk])
        data = {'group': self.group.name, 'submit_manage_group': 'submit'}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        redirect_url = reverse('admin:%s_%s_permissions_manage_group' %
                               self.obj_info, args=[self.obj.pk, self.group.id])
        self.assertEqual(response.request['PATH_INFO'], redirect_url)

    @unittest.skipIf(DJANGO_VERSION >= (3, 0) and
                     "mysql" in os.environ.get("DATABASE_URL", ""),
                     "Negative ids no longer work in Django 3.0+ with MySQL.")
    def test_view_manage_negative_group_form(self):
        self._login_superuser()
        url = reverse('admin:%s_%s_permissions' % self.obj_info,
                      args=[self.obj.pk])
        self.group = Group.objects.create(name='neagive_id_group', id=-2010)
        data = {'group': self.group.name, 'submit_manage_group': 'submit'}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)
        redirect_url = reverse('admin:%s_%s_permissions_manage_group' %
                               self.obj_info, args=[self.obj.pk, self.group.id])
        self.assertEqual(response.request['PATH_INFO'], redirect_url)

    def test_view_manage_group_form_wrong_group(self):
        self._login_superuser()
        url = reverse('admin:%s_%s_permissions' % self.obj_info,
                      args=[self.obj.pk])
        data = {'group': 'wrong-group', 'submit_manage_group': 'submit'}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 0)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('group' in response.context['group_form'].errors)

    def test_view_manage_group_form_wrong_field(self):
        self._login_superuser()
        url = reverse('admin:%s_%s_permissions' % self.obj_info,
                      args=[self.obj.pk])
        data = {'group': '<xss>', 'submit_manage_group': 'submit'}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 0)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('group' in response.context['group_form'].errors)

    def test_view_manage_group_form_empty_group(self):
        self._login_superuser()
        url = reverse('admin:%s_%s_permissions' % self.obj_info,
                      args=[self.obj.pk])
        data = {'group': '', 'submit_manage_group': 'submit'}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 0)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('group' in response.context['group_form'].errors)

    def test_view_manage_group_wrong_perms(self):
        self._login_superuser()
        url = reverse('admin:%s_%s_permissions_manage_group' %
                      self.obj_info, args=[self.obj.pk, self.group.id])
        perms = ['change_user']  # This is not self.obj related permission
        data = {'permissions': perms}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('permissions' in response.context['form'].errors)

    def test_view_manage_group(self):
        self._login_superuser()
        url = reverse('admin:%s_%s_permissions_manage_group' %
                      self.obj_info, args=[self.obj.pk, self.group.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        choices = {c[0] for c in
                       response.context['form'].fields['permissions'].choices}
        self.assertEqual(
            {p.codename for p in get_perms_for_model(self.obj)},
            choices,
        )

        # Add some perms and check if changes were persisted
        perms = ['change_%s' % self.obj_info[
            1], 'delete_%s' % self.obj_info[1]]
        data = {'permissions': perms}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)

        self.assertEqual(
            set(get_perms(self.group, self.obj)),
            set(perms),
        )

        # Remove perm and check if change was persisted
        perms = ['delete_%s' % self.obj_info[1]]
        data = {'permissions': perms}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)

        self.assertEqual(
            set(get_perms(self.group, self.obj)),
            set(perms),
        )

if 'django.contrib.admin' not in settings.INSTALLED_APPS:
    # Skip admin tests if admin app is not registered
    # we simpy clean up AdminTests class ...
    # TODO: use @unittest.skipUnless('django.contrib.admin' in settings.INSTALLED_APPS)
    #       if possible (requires Python 2.7, though)
    AdminTests = type('AdminTests', (TestCase,), {})  # pyflakes:ignore


@skipUnlessTestApp
class GuardedModelAdminTests(TestCase):

    def _get_gma(self, attrs=None, name=None, model=None):
        """
        Returns ``GuardedModelAdmin`` instance.
        """
        attrs = attrs or {}
        name = str(name or 'GMA')
        model = model or User
        GMA = type(name, (GuardedModelAdmin,), attrs)
        gma = GMA(model, admin.site)
        return gma

    def test_obj_perms_manage_template_attr(self):
        attrs = {'obj_perms_manage_template': 'foobar.html'}
        gma = self._get_gma(attrs=attrs)
        self.assertTrue(gma.get_obj_perms_manage_template(), 'foobar.html')

    def test_obj_perms_manage_user_template_attr(self):
        attrs = {'obj_perms_manage_user_template': 'foobar.html'}
        gma = self._get_gma(attrs=attrs)
        self.assertTrue(
            gma.get_obj_perms_manage_user_template(), 'foobar.html')

    def test_obj_perms_manage_user_form_attr(self):
        attrs = {'obj_perms_manage_user_form': forms.Form}
        gma = self._get_gma(attrs=attrs)
        self.assertTrue(issubclass(gma.get_obj_perms_manage_user_form(None), forms.Form))

    def test_obj_perms_user_select_form_attr(self):
        attrs = {'obj_perms_user_select_form': forms.Form}
        gma = self._get_gma(attrs=attrs)
        self.assertTrue(issubclass(gma.get_obj_perms_user_select_form(None), forms.Form))

    def test_obj_perms_manage_group_template_attr(self):
        attrs = {'obj_perms_manage_group_template': 'foobar.html'}
        gma = self._get_gma(attrs=attrs)
        self.assertTrue(gma.get_obj_perms_manage_group_template(),
                        'foobar.html')

    def test_obj_perms_manage_group_form_attr(self):
        attrs = {'obj_perms_manage_group_form': forms.Form}
        gma = self._get_gma(attrs=attrs)
        self.assertTrue(issubclass(gma.get_obj_perms_manage_group_form(None), forms.Form))

    def test_obj_perms_group_select_form_attr(self):
        attrs = {'obj_perms_group_select_form': forms.Form}
        gma = self._get_gma(attrs=attrs)
        self.assertTrue(issubclass(gma.get_obj_perms_group_select_form(None), forms.Form))

    def test_user_can_acces_owned_objects_only(self):
        attrs = {
            'user_can_access_owned_objects_only': True,
            'user_owned_objects_field': 'user',
        }
        gma = self._get_gma(attrs=attrs, model=LogEntry)
        joe = User.objects.create_user('joe', 'joe@example.com', 'joe')
        jane = User.objects.create_user('jane', 'jane@example.com', 'jane')
        ctype = ContentType.objects.get_for_model(User)
        joe_entry = LogEntry.objects.create(user=joe, content_type=ctype,
                                            object_id=joe.pk, action_flag=1, change_message='foo')
        LogEntry.objects.create(user=jane, content_type=ctype,
                                object_id=jane.pk, action_flag=1, change_message='bar')
        request = HttpRequest()
        request.user = joe
        qs = gma.get_queryset(request)
        self.assertEqual([e.pk for e in qs], [joe_entry.pk])

    def test_user_can_acces_owned_objects_only_unless_superuser(self):
        attrs = {
            'user_can_access_owned_objects_only': True,
            'user_owned_objects_field': 'user',
        }
        gma = self._get_gma(attrs=attrs, model=LogEntry)
        joe = User.objects.create_superuser('joe', 'joe@example.com', 'joe')
        jane = User.objects.create_user('jane', 'jane@example.com', 'jane')
        ctype = ContentType.objects.get_for_model(User)
        joe_entry = LogEntry.objects.create(user=joe, content_type=ctype,
                                            object_id=joe.pk, action_flag=1, change_message='foo')
        jane_entry = LogEntry.objects.create(user=jane, content_type=ctype,
                                             object_id=jane.pk, action_flag=1, change_message='bar')
        request = HttpRequest()
        request.user = joe
        qs = gma.get_queryset(request)
        self.assertEqual(sorted([e.pk for e in qs]),
                         sorted([joe_entry.pk, jane_entry.pk]))

    def test_user_can_access_owned_by_group_objects_only(self):
        attrs = {
            'user_can_access_owned_by_group_objects_only': True,
            'group_owned_objects_field': 'group',
        }
        gma = self._get_gma(attrs=attrs, model=LogEntry)
        joe = User.objects.create_user('joe', 'joe@example.com', 'joe')
        joe_group = Group.objects.create(name='joe-group')
        joe.groups.add(joe_group)
        jane = User.objects.create_user('jane', 'jane@example.com', 'jane')
        jane_group = Group.objects.create(name='jane-group')
        jane.groups.add(jane_group)
        ctype = ContentType.objects.get_for_model(User)
        LogEntry.objects.create(user=joe, content_type=ctype,
                                object_id=joe.pk, action_flag=1, change_message='foo')
        LogEntry.objects.create(user=jane, content_type=ctype,
                                object_id=jane.pk, action_flag=1, change_message='bar')
        joe_entry_group = LogEntry.objects.create(user=jane, content_type=ctype,
                                                  object_id=joe.pk, action_flag=1, change_message='foo',
                                                  group=joe_group)
        request = HttpRequest()
        request.user = joe
        qs = gma.get_queryset(request)
        self.assertEqual([e.pk for e in qs], [joe_entry_group.pk])

    def test_user_can_access_owned_by_group_objects_only_unless_superuser(self):
        attrs = {
            'user_can_access_owned_by_group_objects_only': True,
            'group_owned_objects_field': 'group',
        }
        gma = self._get_gma(attrs=attrs, model=LogEntry)
        joe = User.objects.create_superuser('joe', 'joe@example.com', 'joe')
        joe_group = Group.objects.create(name='joe-group')
        joe.groups.add(joe_group)
        jane = User.objects.create_user('jane', 'jane@example.com', 'jane')
        jane_group = Group.objects.create(name='jane-group')
        jane.groups.add(jane_group)
        ctype = ContentType.objects.get_for_model(User)
        LogEntry.objects.create(user=joe, content_type=ctype,
                                object_id=joe.pk, action_flag=1, change_message='foo')
        LogEntry.objects.create(user=jane, content_type=ctype,
                                object_id=jane.pk, action_flag=1, change_message='bar')
        LogEntry.objects.create(user=jane, content_type=ctype,
                                object_id=joe.pk, action_flag=1, change_message='foo',
                                group=joe_group)
        LogEntry.objects.create(user=joe, content_type=ctype,
                                object_id=joe.pk, action_flag=1, change_message='foo',
                                group=jane_group)
        request = HttpRequest()
        request.user = joe
        qs = gma.get_queryset(request)
        self.assertEqual(sorted(e.pk for e in qs),
                         sorted(LogEntry.objects.values_list('pk', flat=True)))


class GrappelliGuardedModelAdminTests(TestCase):

    org_installed_apps = copy.copy(settings.INSTALLED_APPS)

    def _get_gma(self, attrs=None, name=None, model=None):
        """
        Returns ``GuardedModelAdmin`` instance.
        """
        attrs = attrs or {}
        name = str(name or 'GMA')
        model = model or User
        GMA = type(name, (GuardedModelAdmin,), attrs)
        gma = GMA(model, admin.site)
        return gma

    def setUp(self):
        settings.INSTALLED_APPS = ['grappelli'] + list(settings.INSTALLED_APPS)

    def tearDown(self):
        settings.INSTALLED_APPS = self.org_installed_apps

    def test_get_obj_perms_manage_template(self):
        gma = self._get_gma()
        self.assertEqual(gma.get_obj_perms_manage_template(),
                         'admin/guardian/contrib/grappelli/obj_perms_manage.html')

    def test_get_obj_perms_manage_user_template(self):
        gma = self._get_gma()
        self.assertEqual(gma.get_obj_perms_manage_user_template(),
                         'admin/guardian/contrib/grappelli/obj_perms_manage_user.html')

    def test_get_obj_perms_manage_group_template(self):
        gma = self._get_gma()
        self.assertEqual(gma.get_obj_perms_manage_group_template(),
                         'admin/guardian/contrib/grappelli/obj_perms_manage_group.html')
