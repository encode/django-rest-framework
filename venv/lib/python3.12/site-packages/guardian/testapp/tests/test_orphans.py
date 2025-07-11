from django.apps import apps as django_apps
auth_app = django_apps.get_app_config("auth")

from django.contrib.auth import get_user_model
from django.contrib.auth.management import create_permissions
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.test import TestCase

from guardian.utils import clean_orphan_obj_perms
from guardian.shortcuts import assign_perm
from guardian.models import Group
from guardian.testapp.tests.conf import skipUnlessTestApp


User = get_user_model()
user_module_name = User._meta.model_name


@skipUnlessTestApp
class OrphanedObjectPermissionsTest(TestCase):

    def setUp(self):
        # Create objects for which we would assing obj perms
        self.target_user1 = User.objects.create(username='user1')
        self.target_group1 = Group.objects.create(name='group1')
        self.target_obj1 = ContentType.objects.create(
            model='foo', app_label='fake-for-guardian-tests')
        self.target_obj2 = ContentType.objects.create(
            model='bar', app_label='fake-for-guardian-tests')
        # Required if MySQL backend is used :/
        create_permissions(auth_app, 1)

        self.user = User.objects.create(username='user')
        self.group = Group.objects.create(name='group')

    def test_clean_perms(self):

        # assign obj perms
        target_perms = {
            self.target_user1: ["change_%s" % user_module_name],
            self.target_group1: ["delete_group"],
            self.target_obj1: ["change_contenttype", "delete_contenttype"],
            self.target_obj2: ["change_contenttype"],
        }
        obj_perms_count = sum([len(val) for key, val in target_perms.items()])
        for target, perms in target_perms.items():
            target.__old_pk = target.pk  # Store pkeys
            for perm in perms:
                assign_perm(perm, self.user, target)

        # Remove targets
        for target, perms in target_perms.items():
            target.delete()

        # Clean orphans
        removed = clean_orphan_obj_perms()
        self.assertEqual(removed, obj_perms_count)

        # Recreate targets and check if user has no permissions
        for target, perms in target_perms.items():
            target.pk = target.__old_pk
            target.save()
            for perm in perms:
                self.assertFalse(self.user.has_perm(perm, target))

    def test_clean_perms_command(self):
        """
        Same test as the one above but rather function directly, we call
        management command instead.
        """

        # assign obj perms
        target_perms = {
            self.target_user1: ["change_%s" % user_module_name],
            self.target_group1: ["delete_group"],
            self.target_obj1: ["change_contenttype", "delete_contenttype"],
            self.target_obj2: ["change_contenttype"],
        }
        for target, perms in target_perms.items():
            target.__old_pk = target.pk  # Store pkeys
            for perm in perms:
                assign_perm(perm, self.user, target)

        # Remove targets
        for target, perms in target_perms.items():
            target.delete()

        # Clean orphans
        call_command("clean_orphan_obj_perms", verbosity=0)

        # Recreate targets and check if user has no permissions
        for target, perms in target_perms.items():
            target.pk = target.__old_pk
            target.save()
            for perm in perms:
                self.assertFalse(self.user.has_perm(perm, target))
