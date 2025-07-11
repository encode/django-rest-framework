from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from guardian.shortcuts import assign_perm, remove_perm


class CustomPKModelTest(TestCase):
    """
    Tests against custom model with primary key other than *standard*
    ``id`` integer field.
    """

    def setUp(self):
        self.user = get_user_model().objects.create(username='joe')
        self.ctype = ContentType.objects.create(
            model='bar', app_label='fake-for-guardian-tests')

    def test_assign_perm(self):
        assign_perm('contenttypes.change_contenttype', self.user, self.ctype)
        self.assertTrue(self.user.has_perm('contenttypes.change_contenttype',
                                           self.ctype))

    def test_remove_perm(self):
        assign_perm('contenttypes.change_contenttype', self.user, self.ctype)
        self.assertTrue(self.user.has_perm('contenttypes.change_contenttype',
                                           self.ctype))
        remove_perm('contenttypes.change_contenttype', self.user, self.ctype)
        self.assertFalse(self.user.has_perm('contenttypes.change_contenttype',
                                            self.ctype))
