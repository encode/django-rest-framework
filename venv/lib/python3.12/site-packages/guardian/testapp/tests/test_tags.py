from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.template import Template, Context, TemplateSyntaxError
from django.test import TestCase

from guardian.core import ObjectPermissionChecker
from guardian.exceptions import NotUserNorGroup
from guardian.models import UserObjectPermission, GroupObjectPermission

User = get_user_model()


def render(template, context):
    """
    Returns rendered ``template`` with ``context``, which are given as string
    and dict respectively.
    """
    t = Template(template)
    return t.render(Context(context))


class GetObjPermsTagTest(TestCase):

    def setUp(self):
        self.ctype = ContentType.objects.create(
            model='bar', app_label='fake-for-guardian-tests')
        self.group = Group.objects.create(name='jackGroup')
        self.user = User.objects.create(username='jack')
        self.user.groups.add(self.group)

    def test_wrong_formats(self):
        wrong_formats = (
            '{% get_obj_perms user for contenttype as obj_perms %}',  # no quotes
            '{% get_obj_perms user for contenttype as \'obj_perms" %}',  # wrong quotes
            '{% get_obj_perms user for contenttype as \'obj_perms" %}',  # wrong quotes
            '{% get_obj_perms user for contenttype as obj_perms" %}',  # wrong quotes
            '{% get_obj_perms user for contenttype as obj_perms\' %}',  # wrong quotes
            '{% get_obj_perms user for contenttype as %}',  # no context_var
            '{% get_obj_perms for contenttype as "obj_perms" %}',  # no user/group
            '{% get_obj_perms user contenttype as "obj_perms" %}',  # no "for" bit
            '{% get_obj_perms user for contenttype "obj_perms" %}',  # no "as" bit
            '{% get_obj_perms user for as "obj_perms" %}',  # no object
        )

        context = {'user': User.get_anonymous(), 'contenttype': self.ctype}
        for wrong in wrong_formats:
            fullwrong = '{% load guardian_tags %}' + wrong
            try:
                render(fullwrong, context)
                self.fail("Used wrong get_obj_perms tag format: \n\n\t%s\n\n "
                          "but TemplateSyntaxError have not been raised" % wrong)
            except TemplateSyntaxError:
                pass

    def test_obj_none(self):
        template = ''.join((
            '{% load guardian_tags %}',
            '{% get_obj_perms user for object as "obj_perms" %}{{ perms }}',
        ))
        context = {'user': User.get_anonymous(), 'object': None}
        output = render(template, context)
        self.assertEqual(output, '')

    def test_anonymous_user(self):
        template = ''.join((
            '{% load guardian_tags %}',
            '{% get_obj_perms user for contenttype as "obj_perms" %}{{ perms }}',
        ))
        context = {'user': AnonymousUser(), 'contenttype': self.ctype}
        anon_output = render(template, context)
        context = {'user': User.get_anonymous(), 'contenttype': self.ctype}
        real_anon_user_output = render(template, context)
        self.assertEqual(anon_output, real_anon_user_output)

    def test_wrong_user_or_group(self):
        template = ''.join((
            '{% load guardian_tags %}',
            '{% get_obj_perms some_obj for contenttype as "obj_perms" %}',
        ))
        context = {'some_obj': ContentType(), 'contenttype': self.ctype}
        # This test would raise TemplateSyntaxError instead of NotUserNorGroup
        # if the template option 'debug' is set to True during tests.
        template_options = settings.TEMPLATES[0]['OPTIONS']
        tmp = template_options.get('debug', False)
        template_options['debug'] = False
        self.assertRaises(NotUserNorGroup, render, template, context)
        template_options['debug'] = tmp

    def test_superuser(self):
        user = User.objects.create(username='superuser', is_superuser=True)
        template = ''.join((
            '{% load guardian_tags %}',
            '{% get_obj_perms user for contenttype as "obj_perms" %}',
            '{{ obj_perms|join:" " }}',
        ))
        context = {'user': user, 'contenttype': self.ctype}
        output = render(template, context)

        for perm in ('add_contenttype', 'change_contenttype', 'delete_contenttype'):
            self.assertTrue(perm in output)

    def test_user(self):
        UserObjectPermission.objects.assign_perm("change_contenttype", self.user,
                                                 self.ctype)
        GroupObjectPermission.objects.assign_perm("delete_contenttype", self.group,
                                                  self.ctype)

        template = ''.join((
            '{% load guardian_tags %}',
            '{% get_obj_perms user for contenttype as "obj_perms" %}',
            '{{ obj_perms|join:" " }}',
        ))
        context = {'user': self.user, 'contenttype': self.ctype}
        output = render(template, context)

        self.assertEqual(
            set(output.split(' ')),
            set('change_contenttype delete_contenttype'.split(' ')))

    def test_group(self):
        GroupObjectPermission.objects.assign_perm("delete_contenttype", self.group,
                                                  self.ctype)

        template = ''.join((
            '{% load guardian_tags %}',
            '{% get_obj_perms group for contenttype as "obj_perms" %}',
            '{{ obj_perms|join:" " }}',
        ))
        context = {'group': self.group, 'contenttype': self.ctype}
        output = render(template, context)

        self.assertEqual(output, 'delete_contenttype')

    def test_checker(self):
        GroupObjectPermission.objects.assign_perm("delete_contenttype", self.group,
                                                          self.ctype)

        checker = ObjectPermissionChecker(self.user)
        checker.prefetch_perms(Group.objects.all())

        template = ''.join((
            '{% load guardian_tags %}',
            '{% get_obj_perms group for contenttype as "obj_perms" checker %}',
            '{{ obj_perms|join:" " }}',
        ))
        context = {'group': self.group, 'contenttype': self.ctype, 'checker': checker}
        output = render(template, context)

        self.assertEqual(output, 'delete_contenttype')
