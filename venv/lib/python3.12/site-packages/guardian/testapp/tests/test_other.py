from unittest import mock
import unittest

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.test import TestCase

import guardian
from guardian.backends import ObjectPermissionBackend
from guardian.compat import get_user_model_path
from guardian.compat import get_user_permission_codename
from guardian.exceptions import GuardianError
from guardian.exceptions import NotUserNorGroup
from guardian.exceptions import ObjectNotPersisted
from guardian.exceptions import WrongAppError
from guardian.models import GroupObjectPermission
from guardian.models import UserObjectPermission
from guardian.testapp.tests.conf import TestDataMixin
User = get_user_model()
user_model_path = get_user_model_path()


class UserPermissionTests(TestDataMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.user = User.objects.get(username='jack')
        self.ctype = ContentType.objects.create(
            model='bar', app_label='fake-for-guardian-tests')
        self.obj1 = ContentType.objects.create(
            model='foo', app_label='guardian-tests')
        self.obj2 = ContentType.objects.create(
            model='bar', app_label='guardian-tests')

    def test_assignement(self):
        self.assertFalse(self.user.has_perm('change_contenttype', self.ctype))

        UserObjectPermission.objects.assign_perm('change_contenttype', self.user,
                                                 self.ctype)
        self.assertTrue(self.user.has_perm('change_contenttype', self.ctype))
        self.assertTrue(self.user.has_perm('contenttypes.change_contenttype',
                                           self.ctype))

    def test_assignement_and_remove(self):
        UserObjectPermission.objects.assign_perm('change_contenttype', self.user,
                                                 self.ctype)
        self.assertTrue(self.user.has_perm('change_contenttype', self.ctype))

        UserObjectPermission.objects.remove_perm('change_contenttype',
                                                 self.user, self.ctype)
        self.assertFalse(self.user.has_perm('change_contenttype', self.ctype))

    def test_ctypes(self):
        UserObjectPermission.objects.assign_perm(
            'change_contenttype', self.user, self.obj1)
        self.assertTrue(self.user.has_perm('change_contenttype', self.obj1))
        self.assertFalse(self.user.has_perm('change_contenttype', self.obj2))

        UserObjectPermission.objects.remove_perm(
            'change_contenttype', self.user, self.obj1)
        UserObjectPermission.objects.assign_perm(
            'change_contenttype', self.user, self.obj2)
        self.assertTrue(self.user.has_perm('change_contenttype', self.obj2))
        self.assertFalse(self.user.has_perm('change_contenttype', self.obj1))

        UserObjectPermission.objects.assign_perm(
            'change_contenttype', self.user, self.obj1)
        UserObjectPermission.objects.assign_perm(
            'change_contenttype', self.user, self.obj2)
        self.assertTrue(self.user.has_perm('change_contenttype', self.obj2))
        self.assertTrue(self.user.has_perm('change_contenttype', self.obj1))

        UserObjectPermission.objects.remove_perm(
            'change_contenttype', self.user, self.obj1)
        UserObjectPermission.objects.remove_perm(
            'change_contenttype', self.user, self.obj2)
        self.assertFalse(self.user.has_perm('change_contenttype', self.obj2))
        self.assertFalse(self.user.has_perm('change_contenttype', self.obj1))

    def test_assign_perm_validation(self):
        self.assertRaises(Permission.DoesNotExist,
                          UserObjectPermission.objects.assign_perm, 'change_group', self.user,
                          self.user)

        group = Group.objects.create(name='test_group_assign_perm_validation')
        ctype = ContentType.objects.get_for_model(group)
        user_ctype = ContentType.objects.get_for_model(self.user)
        codename = get_user_permission_codename('change')
        perm = Permission.objects.get(
            codename=codename, content_type=user_ctype)

        create_info = dict(
            permission=perm,
            user=self.user,
            content_type=ctype,
            object_pk=group.pk
        )
        self.assertRaises(ValidationError, UserObjectPermission.objects.create,
                          **create_info)

    def test_errors(self):
        not_saved_user = User(username='not_saved_user')
        codename = get_user_permission_codename('change')
        self.assertRaises(ObjectNotPersisted,
                          UserObjectPermission.objects.assign_perm,
                          codename, self.user, not_saved_user)
        self.assertRaises(ObjectNotPersisted,
                          UserObjectPermission.objects.remove_perm,
                          codename, self.user, not_saved_user)


class GroupPermissionTests(TestDataMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.user = User.objects.get(username='jack')
        self.group, created = Group.objects.get_or_create(name='jackGroup')
        self.user.groups.add(self.group)
        self.ctype = ContentType.objects.create(
            model='bar', app_label='fake-for-guardian-tests')
        self.obj1 = ContentType.objects.create(
            model='foo', app_label='guardian-tests')
        self.obj2 = ContentType.objects.create(
            model='bar', app_label='guardian-tests')

    def test_assignement(self):
        self.assertFalse(self.user.has_perm('change_contenttype', self.ctype))
        self.assertFalse(self.user.has_perm('contenttypes.change_contenttype',
                                            self.ctype))

        GroupObjectPermission.objects.assign_perm('change_contenttype', self.group,
                                                  self.ctype)
        self.assertTrue(self.user.has_perm('change_contenttype', self.ctype))
        self.assertTrue(self.user.has_perm('contenttypes.change_contenttype',
                                           self.ctype))

    def test_assignement_and_remove(self):
        GroupObjectPermission.objects.assign_perm('change_contenttype', self.group,
                                                  self.ctype)
        self.assertTrue(self.user.has_perm('change_contenttype', self.ctype))

        GroupObjectPermission.objects.remove_perm('change_contenttype',
                                                  self.group, self.ctype)
        self.assertFalse(self.user.has_perm('change_contenttype', self.ctype))

    def test_ctypes(self):
        GroupObjectPermission.objects.assign_perm('change_contenttype', self.group,
                                                  self.obj1)
        self.assertTrue(self.user.has_perm('change_contenttype', self.obj1))
        self.assertFalse(self.user.has_perm('change_contenttype', self.obj2))

        GroupObjectPermission.objects.remove_perm('change_contenttype',
                                                  self.group, self.obj1)
        GroupObjectPermission.objects.assign_perm('change_contenttype', self.group,
                                                  self.obj2)
        self.assertTrue(self.user.has_perm('change_contenttype', self.obj2))
        self.assertFalse(self.user.has_perm('change_contenttype', self.obj1))

        GroupObjectPermission.objects.assign_perm('change_contenttype', self.group,
                                                  self.obj1)
        GroupObjectPermission.objects.assign_perm('change_contenttype', self.group,
                                                  self.obj2)
        self.assertTrue(self.user.has_perm('change_contenttype', self.obj2))
        self.assertTrue(self.user.has_perm('change_contenttype', self.obj1))

        GroupObjectPermission.objects.remove_perm('change_contenttype',
                                                  self.group, self.obj1)
        GroupObjectPermission.objects.remove_perm('change_contenttype',
                                                  self.group, self.obj2)
        self.assertFalse(self.user.has_perm('change_contenttype', self.obj2))
        self.assertFalse(self.user.has_perm('change_contenttype', self.obj1))

    def test_assign_perm_validation(self):
        self.assertRaises(Permission.DoesNotExist,
                          GroupObjectPermission.objects.assign_perm, 'change_user', self.group,
                          self.group)

        user = User.objects.create(username='testuser')
        ctype = ContentType.objects.get_for_model(user)
        perm = Permission.objects.get(codename='change_group')

        create_info = dict(
            permission=perm,
            group=self.group,
            content_type=ctype,
            object_pk=user.pk
        )
        self.assertRaises(ValidationError, GroupObjectPermission.objects.create,
                          **create_info)

    def test_errors(self):
        not_saved_group = Group(name='not_saved_group')
        self.assertRaises(ObjectNotPersisted,
                          GroupObjectPermission.objects.assign_perm,
                          "change_group", self.group, not_saved_group)
        self.assertRaises(ObjectNotPersisted,
                          GroupObjectPermission.objects.remove_perm,
                          "change_group", self.group, not_saved_group)


class ObjectPermissionBackendTests(TestCase):

    def setUp(self):
        self.user = User.objects.create(username='jack')
        self.backend = ObjectPermissionBackend()

    def test_attrs(self):
        self.assertTrue(self.backend.supports_anonymous_user)
        self.assertTrue(self.backend.supports_object_permissions)
        self.assertTrue(self.backend.supports_inactive_user)

    def test_authenticate(self):
        self.assertEqual(
            self.backend.authenticate(
                request={},
                username=self.user.username,
                password=self.user.password
            ),
            None
        )

    def test_has_perm_noobj(self):
        result = self.backend.has_perm(self.user, "change_contenttype")
        self.assertFalse(result)

    def test_has_perm_notauthed(self):
        user = AnonymousUser()
        self.assertFalse(self.backend.has_perm(user, "change_user", self.user))

    def test_has_perm_wrong_app(self):
        self.assertRaises(WrongAppError, self.backend.has_perm,
                          self.user, "no_app.change_user", self.user)

    def test_obj_is_not_model(self):
        for obj in (Group, 666, "String", [2, 1, 5, 7], {}):
            self.assertFalse(self.backend.has_perm(self.user,
                                                   "any perm", obj))

    def test_not_active_user(self):
        user = User.objects.create(username='non active user')
        ctype = ContentType.objects.create(
            model='bar', app_label='fake-for-guardian-tests')
        perm = 'change_contenttype'
        UserObjectPermission.objects.assign_perm(perm, user, ctype)
        self.assertTrue(self.backend.has_perm(user, perm, ctype))
        user.is_active = False
        user.save()
        self.assertFalse(self.backend.has_perm(user, perm, ctype))


class GuardianBaseTests(TestCase):

    def has_attrs(self):
        self.assertTrue(hasattr(guardian, '__version__'))

    def test_version(self):
        for x in guardian.VERSION:
            self.assertTrue(isinstance(x, (int, str)))

    def test_get_version(self):
        self.assertTrue(isinstance(guardian.get_version(), str))


class TestExceptions(TestCase):

    def _test_error_class(self, exc_cls):
        self.assertTrue(isinstance(exc_cls, GuardianError))

    def test_error_classes(self):
        self.assertTrue(isinstance(GuardianError(), Exception))
        guardian_errors = [NotUserNorGroup]
        for err in guardian_errors:
            self._test_error_class(err())


@unittest.skip("test is broken")
class TestMonkeyPatch(TestCase):

    @mock.patch('django.contrib.auth.get_user_model')
    def test_monkey_patch(self, mocked_get_user_model):

        class CustomUserTestClass(AbstractUser):
            pass

        mocked_get_user_model.return_value = CustomUserTestClass

        self.assertFalse(getattr(CustomUserTestClass, 'get_anonymous', False))
        self.assertFalse(getattr(CustomUserTestClass, 'add_obj_perm', False))
        self.assertFalse(getattr(CustomUserTestClass, 'del_obj_perm', False))
        self.assertFalse(getattr(CustomUserTestClass, 'evict_obj_perms_cache', False))

        # Monkey Patch
        guardian.monkey_patch_user()

        self.assertTrue(getattr(CustomUserTestClass, 'get_anonymous', False))
        self.assertTrue(getattr(CustomUserTestClass, 'add_obj_perm', False))
        self.assertTrue(getattr(CustomUserTestClass, 'del_obj_perm', False))
        self.assertTrue(getattr(CustomUserTestClass, 'evict_obj_perms_cache', False))

        user = CustomUserTestClass()
        self.assertFalse(user.evict_obj_perms_cache())
