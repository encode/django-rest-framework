from itertools import chain

from django.conf import settings
from guardian.conf import settings as guardian_settings
from django.apps import apps as django_apps
from django.contrib.auth import get_user_model
from django.contrib.auth.management import create_permissions
from django.contrib.auth.models import Group, Permission, AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from guardian.core import ObjectPermissionChecker
from guardian.exceptions import NotUserNorGroup
from guardian.models import UserObjectPermission, GroupObjectPermission
from guardian.shortcuts import assign_perm
from guardian.management import create_anonymous_user
from guardian.utils import evict_obj_perms_cache

from guardian.testapp.models import Project, ProjectUserObjectPermission, ProjectGroupObjectPermission

auth_app = django_apps.get_app_config('auth')
User = get_user_model()


class CustomUserTests(TestCase):

    def test_create_anonymous_user(self):
        create_anonymous_user(object(), using='default')
        self.assertEqual(1, User.objects.all().count())
        anonymous = User.objects.all()[0]
        self.assertEqual(anonymous.username, guardian_settings.ANONYMOUS_USER_NAME)


class ObjectPermissionTestCase(TestCase):

    def setUp(self):
        self.group, created = Group.objects.get_or_create(name='jackGroup')
        self.user, created = User.objects.get_or_create(username='jack')
        self.user.groups.add(self.group)
        self.ctype = ContentType.objects.create(
            model='bar', app_label='fake-for-guardian-tests')
        self.ctype_qset = ContentType.objects.filter(model='bar',
                                                     app_label='fake-for-guardian-tests')
        self.ctype_list = [self.ctype_qset.first()]
        self.anonymous_user = User.objects.get(
            username=guardian_settings.ANONYMOUS_USER_NAME)

    def get_permission(self, codename, app_label=None):
        qs = Permission.objects
        if app_label:
            qs = qs.filter(content_type__app_label=app_label)
        return Permission.objects.get(codename=codename)


class ObjectPermissionCheckerTest(ObjectPermissionTestCase):

    def setUp(self):
        super().setUp()
        # Required if MySQL backend is used :/
        create_permissions(auth_app, 1)

    def test_cache_for_queries_count(self):
        settings.DEBUG = True
        try:
            from django.db import connection

            ContentType.objects.clear_cache()
            checker = ObjectPermissionChecker(self.user)

            # has_perm on Checker should spawn only two queries plus one extra
            # for fetching the content type first time we check for specific
            # model and two more content types as there are additional checks
            # at get_user_obj_perms_model and get_group_obj_perms_model
            query_count = len(connection.queries)
            res = checker.has_perm("change_group", self.group)
            if 'guardian.testapp' in settings.INSTALLED_APPS:
                expected = 5
            else:
                # TODO: This is strange, need to investigate; totally not sure
                # why there are more queries if testapp is not included
                expected = 11
            self.assertEqual(len(connection.queries), query_count + expected)

            # Checking again shouldn't spawn any queries
            query_count = len(connection.queries)
            res_new = checker.has_perm("change_group", self.group)
            self.assertEqual(res, res_new)
            self.assertEqual(len(connection.queries), query_count)

            # Checking for other permission but for Group object again
            # shouldn't spawn any query too
            query_count = len(connection.queries)
            checker.has_perm("delete_group", self.group)
            self.assertEqual(len(connection.queries), query_count)

            # Checking for same model but other instance should spawn 2 queries
            new_group = Group.objects.create(name='new-group')
            query_count = len(connection.queries)
            checker.has_perm("change_group", new_group)
            self.assertEqual(len(connection.queries), query_count + 2)

            # Checking for permission for other model should spawn 4 queries
            # every added direct relation adds one more query..
            # (again: content type and actual permissions for the object...
            query_count = len(connection.queries)
            checker.has_perm("change_user", self.user)
            self.assertEqual(len(connection.queries), query_count + 4)

        finally:
            settings.DEBUG = False

    def test_init(self):
        self.assertRaises(NotUserNorGroup, ObjectPermissionChecker,
                          user_or_group=ContentType())
        self.assertRaises(NotUserNorGroup, ObjectPermissionChecker)

    def test_anonymous_user(self):
        user = AnonymousUser()
        check = ObjectPermissionChecker(user)
        # assert anonymous user has no object permissions at all for obj
        self.assertTrue([] == list(check.get_perms(self.ctype)))

    def test_superuser(self):
        user = User.objects.create(username='superuser', is_superuser=True)
        check = ObjectPermissionChecker(user)
        ctype = ContentType.objects.get_for_model(self.ctype)
        perms = sorted(chain(*Permission.objects
                             .filter(content_type=ctype)
                             .values_list('codename')))
        self.assertEqual(perms, check.get_perms(self.ctype))
        for perm in perms:
            self.assertTrue(check.has_perm(perm, self.ctype))

    def test_not_active_superuser(self):
        user = User.objects.create(username='not_active_superuser',
                                   is_superuser=True, is_active=False)
        check = ObjectPermissionChecker(user)
        ctype = ContentType.objects.get_for_model(self.ctype)
        perms = sorted(chain(*Permission.objects
                             .filter(content_type=ctype)
                             .values_list('codename')))
        self.assertEqual(check.get_perms(self.ctype), [])
        for perm in perms:
            self.assertFalse(check.has_perm(perm, self.ctype))

    def test_not_active_user(self):
        user = User.objects.create(username='notactive')
        assign_perm("change_contenttype", user, self.ctype)

        # new ObjectPermissionChecker is created for each User.has_perm call
        self.assertTrue(user.has_perm("change_contenttype", self.ctype))
        user.is_active = False
        self.assertFalse(user.has_perm("change_contenttype", self.ctype))

        # use on one checker only (as user's is_active attr should be checked
        # before try to use cache
        user = User.objects.create(username='notactive-cache')
        assign_perm("change_contenttype", user, self.ctype)

        check = ObjectPermissionChecker(user)
        self.assertTrue(check.has_perm("change_contenttype", self.ctype))
        user.is_active = False
        self.assertFalse(check.has_perm("change_contenttype", self.ctype))

    def test_get_perms(self):
        group = Group.objects.create(name='group')
        obj1 = ContentType.objects.create(
            model='foo', app_label='guardian-tests')
        obj2 = ContentType.objects.create(
            model='bar', app_label='guardian-tests')

        assign_perms = {
            group: ('change_group', 'delete_group'),
            obj1: ('change_contenttype', 'delete_contenttype'),
            obj2: ('delete_contenttype',),
        }

        check = ObjectPermissionChecker(self.user)

        for obj, perms in assign_perms.items():
            for perm in perms:
                UserObjectPermission.objects.assign_perm(perm, self.user, obj)
            self.assertEqual(sorted(perms), sorted(check.get_perms(obj)))

        check = ObjectPermissionChecker(self.group)

        for obj, perms in assign_perms.items():
            for perm in perms:
                GroupObjectPermission.objects.assign_perm(
                    perm, self.group, obj)
            self.assertEqual(sorted(perms), sorted(check.get_perms(obj)))

    def test_prefetch_user_perms(self):
        settings.DEBUG = True
        try:
            from django.db import connection

            ContentType.objects.clear_cache()
            group1 = Group.objects.create(name='group1')
            group2 = Group.objects.create(name='group2')
            user = User.objects.create(username='active_user', is_active=True)
            assign_perm("change_group", user, self.group)
            assign_perm("change_group", user, group1)
            checker = ObjectPermissionChecker(user)

            # Prefetch permissions
            prefetched_objects = [self.group, group1, group2]
            self.assertTrue(checker.prefetch_perms(prefetched_objects))
            query_count = len(connection.queries)

            # Checking cache is filled
            self.assertEqual(
                len(checker._obj_perms_cache),
                len(prefetched_objects)
            )

            # Checking shouldn't spawn any queries
            checker.has_perm("change_group", self.group)
            self.assertEqual(len(connection.queries), query_count)

            # Checking for other permission but for Group object again
            # shouldn't spawn any query too
            checker.has_perm("delete_group", self.group)
            self.assertEqual(len(connection.queries), query_count)

            # Checking for same model but other instance shouldn't spawn any queries
            checker.has_perm("change_group", group1)
            self.assertEqual(len(connection.queries), query_count)

            # Checking for same model but other instance shouldn't spawn any queries
            # Even though User doesn't have perms on Group2, we still should
            #  not hit DB
            self.assertFalse(checker.has_perm("change_group", group2))
            self.assertEqual(len(connection.queries), query_count)
        finally:
            settings.DEBUG = False

    def test_prefetch_superuser_perms(self):
        settings.DEBUG = True
        try:
            from django.db import connection

            ContentType.objects.clear_cache()
            group1 = Group.objects.create(name='group1')
            user = User.objects.create(username='active_superuser',
                                       is_superuser=True, is_active=True)
            assign_perm("change_group", user, self.group)
            checker = ObjectPermissionChecker(user)

            # Prefetch permissions
            prefetched_objects = [self.group, group1]
            self.assertTrue(checker.prefetch_perms(prefetched_objects))
            query_count = len(connection.queries)

            # Checking cache is filled
            self.assertEqual(
                len(checker._obj_perms_cache),
                len(prefetched_objects)
            )

            # Checking shouldn't spawn any queries
            checker.has_perm("change_group", self.group)
            self.assertEqual(len(connection.queries), query_count)

            # Checking for other permission but for Group object again
            # shouldn't spawn any query too
            checker.has_perm("delete_group", self.group)
            self.assertEqual(len(connection.queries), query_count)

            # Checking for same model but other instance shouldn't spawn any queries
            checker.has_perm("change_group", group1)
            self.assertEqual(len(connection.queries), query_count)
        finally:
            settings.DEBUG = False

    def test_prefetch_group_perms(self):
        settings.DEBUG = True
        try:
            from django.db import connection

            ContentType.objects.clear_cache()
            group1 = Group.objects.create(name='group1')
            group2 = Group.objects.create(name='group2')
            assign_perm("change_group", group1, self.group)
            assign_perm("change_group", group1, group1)
            checker = ObjectPermissionChecker(group1)

            # Prefetch permissions
            prefetched_objects = [self.group, group1, group2]
            self.assertTrue(checker.prefetch_perms(prefetched_objects))

            query_count = len(connection.queries)

            # Checking cache is filled
            self.assertEqual(
                len(checker._obj_perms_cache),
                len(prefetched_objects)
            )

            # Checking shouldn't spawn any queries
            checker.has_perm("change_group", self.group)
            self.assertEqual(len(connection.queries), query_count)

            # Checking for other permission but for Group object again
            # shouldn't spawn any query too
            checker.has_perm("delete_group", self.group)
            self.assertEqual(len(connection.queries), query_count)

            # Checking for same model but other instance shouldn't spawn any queries
            checker.has_perm("change_group", group1)
            self.assertEqual(len(connection.queries), query_count)

            # Checking for same model but other instance shouldn't spawn any queries
            # Even though User doesn't have perms on Group2, we still should
            #  not hit DB
            self.assertFalse(checker.has_perm("change_group", group2))
            self.assertEqual(len(connection.queries), query_count)
        finally:
            settings.DEBUG = False

    def test_prefetch_user_perms_direct_rel(self):
        settings.DEBUG = True
        try:
            from django.db import connection

            ContentType.objects.clear_cache()
            user = User.objects.create(username='active_user', is_active=True)
            projects = \
                [Project.objects.create(name='Project%s' % i)
                    for i in range(3)]
            assign_perm("change_project", user, projects[0])
            assign_perm("change_project", user, projects[1])

            checker = ObjectPermissionChecker(user)

            # Prefetch permissions
            self.assertTrue(checker.prefetch_perms(projects))
            query_count = len(connection.queries)

            # Checking cache is filled
            self.assertEqual(len(checker._obj_perms_cache), len(projects))

            # Checking shouldn't spawn any queries
            checker.has_perm("change_project", projects[0])
            self.assertEqual(len(connection.queries), query_count)

            # Checking for other permission but for Group object again
            # shouldn't spawn any query too
            checker.has_perm("delete_project", projects[0])
            self.assertEqual(len(connection.queries), query_count)

            # Checking for same model but other instance shouldn't spawn any
            #  queries
            checker.has_perm("change_project", projects[1])
            self.assertEqual(len(connection.queries), query_count)

            # Checking for same model but other instance shouldn't spawn any queries
            # Even though User doesn't have perms on projects[2], we still
            #  should not hit DB
            self.assertFalse(checker.has_perm("change_project", projects[2]))
            self.assertEqual(len(connection.queries), query_count)
        finally:
            settings.DEBUG = False

    def test_prefetch_superuser_perms_direct_rel(self):
        settings.DEBUG = True
        try:
            from django.db import connection

            ContentType.objects.clear_cache()
            user = User.objects.create(
                username='active_user', is_active=True, is_superuser=True)
            projects = \
                [Project.objects.create(name='Project%s' % i)
                    for i in range(2)]
            assign_perm("change_project", user, projects[0])

            checker = ObjectPermissionChecker(user)

            # Prefetch permissions
            self.assertTrue(checker.prefetch_perms(projects))
            query_count = len(connection.queries)

            # Checking cache is filled
            self.assertEqual(len(checker._obj_perms_cache), len(projects))

            # Checking shouldn't spawn any queries
            checker.has_perm("change_project", projects[0])
            self.assertEqual(len(connection.queries), query_count)

            # Checking for other permission but for Group object again
            # shouldn't spawn any query too
            checker.has_perm("delete_project", projects[0])
            self.assertEqual(len(connection.queries), query_count)

            # Checking for same model but other instance shouldn't spawn any
            #  queries
            checker.has_perm("change_project", projects[1])
            self.assertEqual(len(connection.queries), query_count)
        finally:
            settings.DEBUG = False

    def test_prefetch_group_perms_direct_rel(self):
        settings.DEBUG = True
        try:
            from django.db import connection

            ContentType.objects.clear_cache()
            group = Group.objects.create(name='new-group')
            projects = \
                [Project.objects.create(name='Project%s' % i)
                    for i in range(3)]
            assign_perm("change_project", group, projects[0])
            assign_perm("change_project", group, projects[1])

            checker = ObjectPermissionChecker(group)

            # Prefetch permissions
            self.assertTrue(checker.prefetch_perms(projects))
            query_count = len(connection.queries)

            # Checking cache is filled
            self.assertEqual(len(checker._obj_perms_cache), len(projects))

            # Checking shouldn't spawn any queries
            checker.has_perm("change_project", projects[0])
            self.assertEqual(len(connection.queries), query_count)

            # Checking for other permission but for Group object again
            # shouldn't spawn any query too
            checker.has_perm("delete_project", projects[0])
            self.assertEqual(len(connection.queries), query_count)

            # Checking for same model but other instance shouldn't spawn any
            #  queries
            checker.has_perm("change_project", projects[1])
            self.assertEqual(len(connection.queries), query_count)

            # Checking for same model but other instance shouldn't spawn any queries
            # Even though User doesn't have perms on projects[2], we still
            #  should not hit DB
            self.assertFalse(checker.has_perm("change_project", projects[2]))
            self.assertEqual(len(connection.queries), query_count)
        finally:
            settings.DEBUG = False

    def test_autoprefetch_user_perms(self):
        settings.DEBUG = True
        guardian_settings.AUTO_PREFETCH = True
        ProjectUserObjectPermission.enabled = False
        ProjectGroupObjectPermission.enabled = False
        try:
            from django.db import connection

            ContentType.objects.clear_cache()
            group1 = Group.objects.create(name='group1')
            group2 = Group.objects.create(name='group2')
            user = User.objects.create(username='active_user', is_active=True)
            assign_groups = [self.group, group1]
            for group in assign_groups:
                assign_perm("change_group", user, group)

            # Faux monkeypatching
            setattr(User, 'evict_obj_perms_cache', evict_obj_perms_cache)

            # Try to evict non-existent cache, should return false
            self.assertFalse(user.evict_obj_perms_cache())

            checker = ObjectPermissionChecker(user)

            pre_query_count = len(connection.queries)
            # Fill cache
            checker._prefetch_cache()
            query_count = len(connection.queries)

            # Ensure two queries have been made
            self.assertEqual(query_count - pre_query_count, 2)

            # Check user has cache attribute
            self.assertTrue(hasattr(user, '_guardian_perms_cache'))

            # Checking cache is filled
            self.assertEqual(
                len(checker._obj_perms_cache),
                len(assign_groups)
            )

            # Checking shouldn't spawn any queries
            self.assertTrue(checker.has_perm("change_group", self.group))
            self.assertTrue(user.has_perm("change_group", self.group))
            self.assertEqual(len(connection.queries), query_count)

            # Checking for other permission but for Group object again
            # shouldn't spawn any query too
            self.assertFalse(checker.has_perm("delete_group", self.group))
            self.assertFalse(user.has_perm("delete_group", self.group))
            self.assertEqual(len(connection.queries), query_count)

            # Checking for same model but other instance shouldn't spawn any queries
            self.assertTrue(checker.has_perm("change_group", group1))
            self.assertTrue(user.has_perm("change_group", group1))
            self.assertEqual(len(connection.queries), query_count)

            # Checking for same model but other instance shouldn't spawn any queries
            # Even though User doesn't have perms on Group2, we still should
            #  not hit DB
            self.assertFalse(checker.has_perm("change_group", group2))
            self.assertFalse(user.has_perm("change_group", group2))
            self.assertEqual(len(connection.queries), query_count)

            # Evict cache and verify that reloaded perms have changed
            self.assertTrue(user.evict_obj_perms_cache())
            self.assertFalse(hasattr(user, '_guardian_perms_cache'))
            assign_perm("delete_group", user, self.group)
            query_count = len(connection.queries)
            # New checker object so that we reload perms from db
            checker = ObjectPermissionChecker(user)
            self.assertTrue(checker.has_perm("delete_group", self.group))
            self.assertTrue(user.has_perm("delete_group", self.group))
            # Two more queries should have been executed
            self.assertEqual(len(connection.queries), query_count + 2)


        finally:
            settings.DEBUG = False
            guardian_settings.AUTO_PREFETCH = False
            ProjectUserObjectPermission.enabled = True
            ProjectGroupObjectPermission.enabled = True

    def test_autoprefetch_superuser_perms(self):
        settings.DEBUG = True
        guardian_settings.AUTO_PREFETCH = True
        ProjectUserObjectPermission.enabled = False
        ProjectGroupObjectPermission.enabled = False
        try:
            from django.db import connection

            ContentType.objects.clear_cache()
            group1 = Group.objects.create(name='group1')
            user = User.objects.create(username='active_superuser',
                                       is_superuser=True, is_active=True)
            assign_perm("change_group", user, self.group)
            checker = ObjectPermissionChecker(user)

            # Fill cache
            checker._prefetch_cache()
            query_count = len(connection.queries)

            # Check user has cache attribute
            self.assertTrue(hasattr(user, '_guardian_perms_cache'))

            # Checking shouldn't spawn any queries
            self.assertTrue(checker.has_perm("change_group", self.group))
            self.assertTrue(user.has_perm("change_group", self.group))
            self.assertEqual(len(connection.queries), query_count)

            # Checking for other permission but for Group object again
            # shouldn't spawn any query too
            self.assertTrue(checker.has_perm("delete_group", self.group))
            self.assertTrue(user.has_perm("delete_group", self.group))
            self.assertEqual(len(connection.queries), query_count)

            # Checking for same model but other instance shouldn't spawn any queries
            self.assertTrue(checker.has_perm("change_group", group1))
            self.assertTrue(user.has_perm("change_group", group1))
            self.assertEqual(len(connection.queries), query_count)
        finally:
            settings.DEBUG = False
            guardian_settings.AUTO_PREFETCH = False
            ProjectUserObjectPermission.enabled = True
            ProjectGroupObjectPermission.enabled = True

    def test_autoprefetch_group_perms(self):
        settings.DEBUG = True
        guardian_settings.AUTO_PREFETCH = True
        ProjectUserObjectPermission.enabled = False
        ProjectGroupObjectPermission.enabled = False
        try:
            from django.db import connection

            ContentType.objects.clear_cache()
            group = Group.objects.create(name='new-group')
            projects = \
                [Project.objects.create(name='Project%s' % i)
                    for i in range(3)]
            assign_perm("change_project", group, projects[0])
            assign_perm("change_project", group, projects[1])

            checker = ObjectPermissionChecker(group)

            pre_query_count = len(connection.queries)
            # Fill cache
            checker._prefetch_cache()
            query_count = len(connection.queries)

            # Ensure only one query has been made
            self.assertEqual(query_count - pre_query_count, 1)

            # Check group has cache attribute
            self.assertTrue(hasattr(group, '_guardian_perms_cache'))

            # Checking shouldn't spawn any queries
            self.assertTrue(checker.has_perm("change_project", projects[0]))
            self.assertEqual(len(connection.queries), query_count)

            # Checking for other permission but for Group object again
            # shouldn't spawn any query too
            self.assertFalse(checker.has_perm("delete_project", projects[0]))
            self.assertEqual(len(connection.queries), query_count)

            # Checking for same model but other instance shouldn't spawn any
            #  queries
            self.assertTrue(checker.has_perm("change_project", projects[1]))
            self.assertEqual(len(connection.queries), query_count)

            # Checking for same model but other instance shouldn't spawn any queries
            # Even though User doesn't have perms on projects[2], we still
            #  should not hit DB
            self.assertFalse(checker.has_perm("change_project", projects[2]))
            self.assertEqual(len(connection.queries), query_count)
        finally:
            settings.DEBUG = False
            guardian_settings.AUTO_PREFETCH = False
            ProjectUserObjectPermission.enabled = True
            ProjectGroupObjectPermission.enabled = True
