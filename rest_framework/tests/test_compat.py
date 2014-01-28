import django
from django.test import TestCase


class TestCompat(TestCase):
    def test_force_bytes_or_smart_bytes(self):
        from rest_framework.compat import force_bytes_or_smart_bytes
        if django.VERSION >= (1, 5):
            from django.utils.encoding import force_bytes
            self.assertEqual(force_bytes_or_smart_bytes, force_bytes)
        else:
            from django.utils.encoding import smart_str
            self.assertEqual(force_bytes_or_smart_bytes, smart_str)
