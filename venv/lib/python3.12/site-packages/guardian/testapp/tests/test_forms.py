from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from guardian.forms import BaseObjectPermissionsForm


class BaseObjectPermissionsFormTests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            'joe', 'joe@example.com', 'joe')
        self.obj = ContentType.objects.create(
            model='bar', app_label='fake-for-guardian-tests')

    def test_not_implemented(self):

        class MyUserObjectPermissionsForm(BaseObjectPermissionsForm):

            def __init__(formself, user, *args, **kwargs):
                self.user = user
                super().__init__(*args, **kwargs)

        form = MyUserObjectPermissionsForm(self.user, self.obj, {})
        self.assertRaises(NotImplementedError, form.save_obj_perms)

        field_name = form.get_obj_perms_field_name()
        self.assertTrue(form.is_valid())
        self.assertEqual(len(form.cleaned_data[field_name]), 0)
