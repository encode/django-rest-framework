from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase

from guardian.shortcuts import assign_perm
from guardian.shortcuts import get_groups_with_perms
from guardian.shortcuts import get_objects_for_group
from guardian.shortcuts import get_objects_for_user
from guardian.shortcuts import get_users_with_perms
from guardian.shortcuts import remove_perm
from guardian.testapp.models import Mixed, ReverseMixed
from guardian.testapp.models import Project
from guardian.testapp.models import ProjectGroupObjectPermission
from guardian.testapp.models import ProjectUserObjectPermission
from guardian.testapp.tests.conf import skipUnlessTestApp

User = get_user_model()


@skipUnlessTestApp
class TestDirectUserPermissions(TestCase):
    def setUp(self):
        self.joe = User.objects.create_user('joe', 'joe@example.com', 'foobar')
        self.project = Project.objects.create(name='Foobar')

    def get_perm(self, codename):
        filters = {'content_type__app_label': 'testapp', 'codename': codename}
        return Permission.objects.get(**filters)

    def test_after_perm_is_created_without_shortcut(self):
        perm = self.get_perm('add_project')
        # we should not use assign here - if generic user obj perms model is
        # used then everything could go fine if using assign shortcut and we
        # would not be able to see any problem
        ProjectUserObjectPermission.objects.create(
            user=self.joe,
            permission=perm,
            content_object=self.project,
        )
        self.assertTrue(self.joe.has_perm('add_project', self.project))

    def test_assign_perm(self):
        assign_perm('add_project', self.joe, self.project)
        filters = {
            'content_object': self.project,
            'permission__codename': 'add_project',
            'user': self.joe,
        }
        result = ProjectUserObjectPermission.objects.filter(**filters).count()
        self.assertEqual(result, 1)

    def test_remove_perm(self):
        assign_perm('add_project', self.joe, self.project)
        filters = {
            'content_object': self.project,
            'permission__codename': 'add_project',
            'user': self.joe,
        }
        result = ProjectUserObjectPermission.objects.filter(**filters).count()
        self.assertEqual(result, 1)

        remove_perm('add_project', self.joe, self.project)
        result = ProjectUserObjectPermission.objects.filter(**filters).count()
        self.assertEqual(result, 0)

    def test_get_users_with_perms(self):
        User.objects.create_user('john', 'john@foobar.com', 'john')
        jane = User.objects.create_user('jane', 'jane@foobar.com', 'jane')
        assign_perm('add_project', self.joe, self.project)
        assign_perm('change_project', self.joe, self.project)
        assign_perm('change_project', jane, self.project)
        self.assertEqual(get_users_with_perms(self.project, attach_perms=True),
                         {
                             self.joe: ['add_project', 'change_project'],
                             jane: ['change_project'],
                         })

    def test_get_users_with_perms_plus_groups(self):
        User.objects.create_user('john', 'john@foobar.com', 'john')
        jane = User.objects.create_user('jane', 'jane@foobar.com', 'jane')
        group = Group.objects.create(name='devs')
        self.joe.groups.add(group)
        assign_perm('add_project', self.joe, self.project)
        assign_perm('change_project', group, self.project)
        assign_perm('change_project', jane, self.project)
        self.assertEqual(get_users_with_perms(self.project, attach_perms=True),
                         {
                             self.joe: ['add_project', 'change_project'],
                             jane: ['change_project'],
                         })

    def test_get_objects_for_user(self):
        foo = Project.objects.create(name='foo')
        bar = Project.objects.create(name='bar')
        assign_perm('add_project', self.joe, foo)
        assign_perm('add_project', self.joe, bar)
        assign_perm('change_project', self.joe, bar)

        result = get_objects_for_user(self.joe, 'testapp.add_project')
        self.assertEqual(sorted(p.pk for p in result),
                         sorted([foo.pk, bar.pk]))

    def test_get_all_permissions(self):
        foo = Project.objects.create(name='foo')
        assign_perm('add_project', self.joe, foo)
        assign_perm('change_project', self.joe, foo)

        result = self.joe.get_all_permissions(foo)
        self.assertEqual(result, {'add_project', 'change_project'})

    def test_get_all_permissions_no_object(self):
        foo = Project.objects.create(name='foo')
        assign_perm('add_project', self.joe, foo)
        assign_perm('change_project', self.joe, foo)

        result = self.joe.get_all_permissions()
        self.assertEqual(result, set())


@skipUnlessTestApp
class TestDirectGroupPermissions(TestCase):
    def setUp(self):
        self.joe = User.objects.create_user('joe', 'joe@example.com', 'foobar')
        self.group = Group.objects.create(name='admins')
        self.joe.groups.add(self.group)
        self.project = Project.objects.create(name='Foobar')

    def get_perm(self, codename):
        filters = {'content_type__app_label': 'testapp', 'codename': codename}
        return Permission.objects.get(**filters)

    def test_after_perm_is_created_without_shortcut(self):
        perm = self.get_perm('add_project')
        # we should not use assign here - if generic user obj perms model is
        # used then everything could go fine if using assign shortcut and we
        # would not be able to see any problem
        ProjectGroupObjectPermission.objects.create(
            group=self.group,
            permission=perm,
            content_object=self.project,
        )
        self.assertTrue(self.joe.has_perm('add_project', self.project))

    def test_assign_perm(self):
        assign_perm('add_project', self.group, self.project)
        filters = {
            'content_object': self.project,
            'permission__codename': 'add_project',
            'group': self.group,
        }
        result = ProjectGroupObjectPermission.objects.filter(**filters).count()
        self.assertEqual(result, 1)

    def test_remove_perm(self):
        assign_perm('add_project', self.group, self.project)
        filters = {
            'content_object': self.project,
            'permission__codename': 'add_project',
            'group': self.group,
        }
        result = ProjectGroupObjectPermission.objects.filter(**filters).count()
        self.assertEqual(result, 1)

        remove_perm('add_project', self.group, self.project)
        result = ProjectGroupObjectPermission.objects.filter(**filters).count()
        self.assertEqual(result, 0)

    def test_get_groups_with_perms(self):
        Group.objects.create(name='managers')
        devs = Group.objects.create(name='devs')
        assign_perm('add_project', self.group, self.project)
        assign_perm('change_project', self.group, self.project)
        assign_perm('change_project', devs, self.project)
        self.assertEqual(get_groups_with_perms(self.project, attach_perms=True),
                         {
                             self.group: ['add_project', 'change_project'],
                             devs: ['change_project'],
                         })

    def test_get_groups_with_perms_doesnt_spawn_extra_queries_for_more_groups_with_perms(self):
        Group.objects.create(name='managers')
        devs = Group.objects.create(name='devs')
        devs1 = Group.objects.create(name='devs1')
        devs2 = Group.objects.create(name='devs2')
        devs3 = Group.objects.create(name='devs3')
        devs4 = Group.objects.create(name='devs4')
        devs5 = Group.objects.create(name='devs5')
        assign_perm('add_project', self.group, self.project)
        assign_perm('change_project', self.group, self.project)
        for group in [devs, devs1, devs2, devs3, devs4, devs5]:
            assign_perm('add_project', group, self.project)
            assign_perm('change_project', group, self.project)

        with self.assertNumQueries(3):
            result = get_groups_with_perms(self.project, attach_perms=True)

        self.assertEqual(result,
                         {
                             self.group: ['add_project', 'change_project'],
                             devs: ['add_project', 'change_project'],
                             devs1: ['add_project', 'change_project'],
                             devs2: ['add_project', 'change_project'],
                             devs3: ['add_project', 'change_project'],
                             devs4: ['add_project', 'change_project'],
                             devs5: ['add_project', 'change_project'],
                         })

    def test_get_objects_for_group(self):
        foo = Project.objects.create(name='foo')
        bar = Project.objects.create(name='bar')
        assign_perm('add_project', self.group, foo)
        assign_perm('add_project', self.group, bar)
        assign_perm('change_project', self.group, bar)

        result = get_objects_for_group(self.group, 'testapp.add_project')
        self.assertEqual(sorted(p.pk for p in result),
                         sorted([foo.pk, bar.pk]))


@skipUnlessTestApp
class TestMixedDirectAndGenericObjectPermission(TestCase):
    def setUp(self):
        self.joe = User.objects.create_user('joe', 'joe@example.com', 'foobar')
        self.group = Group.objects.create(name='admins')
        self.joe.groups.add(self.group)
        self.mixed = Mixed.objects.create(name='Foobar')
        self.reverse_mixed = ReverseMixed.objects.create(name='Foobar')

    def test_get_users_with_perms_plus_groups(self):
        User.objects.create_user('john', 'john@foobar.com', 'john')
        jane = User.objects.create_user('jane', 'jane@foobar.com', 'jane')
        group = Group.objects.create(name='devs')
        self.joe.groups.add(group)
        assign_perm('add_mixed', self.joe, self.mixed)
        assign_perm('change_mixed', group, self.mixed)
        assign_perm('change_mixed', jane, self.mixed)
        self.assertEqual(get_users_with_perms(self.mixed, attach_perms=True),
                         {
                             self.joe: ['add_mixed', 'change_mixed'],
                             jane: ['change_mixed'],
                         })
        result = get_objects_for_user(self.joe, 'testapp.add_mixed')
        self.assertEqual(sorted(p.pk for p in result),
                         sorted([self.mixed.pk]))

    def test_get_users_with_perms_plus_groups_reverse_mixed(self):
        User.objects.create_user('john', 'john@foobar.com', 'john')
        jane = User.objects.create_user('jane', 'jane@foobar.com', 'jane')
        group = Group.objects.create(name='devs')
        self.joe.groups.add(group)
        assign_perm('add_reversemixed', self.joe, self.reverse_mixed)
        assign_perm('change_reversemixed', group, self.reverse_mixed)
        assign_perm('change_reversemixed', jane, self.reverse_mixed)
        self.assertEqual(get_users_with_perms(self.reverse_mixed, attach_perms=True),
                         {
                             self.joe: ['add_reversemixed', 'change_reversemixed'],
                             jane: ['change_reversemixed'],
                         })
        result = get_objects_for_user(self.joe, 'testapp.add_reversemixed')
        self.assertEqual(sorted(p.pk for p in result),
                         sorted([self.reverse_mixed.pk]))
