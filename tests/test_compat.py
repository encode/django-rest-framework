from django.test import TestCase

from rest_framework import compat


class CompatTests(TestCase):

    def setUp(self):
        self.original_django_version = compat.django.VERSION
        self.original_transaction = compat.transaction

    def tearDown(self):
        compat.django.VERSION = self.original_django_version
        compat.transaction = self.original_transaction

    def test_total_seconds(self):
        class MockTimedelta(object):
            days = 1
            seconds = 1
            microseconds = 100
        timedelta = MockTimedelta()
        expected = (timedelta.days * 86400.0) + float(timedelta.seconds) + (timedelta.microseconds / 1000000.0)
        assert compat.total_seconds(timedelta) == expected

    def test_get_remote_field_with_old_django_version(self):
        class MockField(object):
            rel = 'example_rel'
        compat.django.VERSION = (1, 8)
        assert compat.get_remote_field(MockField(), default='default_value') == 'example_rel'
        assert compat.get_remote_field(object(), default='default_value') == 'default_value'

    def test_get_remote_field_with_new_django_version(self):
        class MockField(object):
            remote_field = 'example_remote_field'
        compat.django.VERSION = (1, 10)
        assert compat.get_remote_field(MockField(), default='default_value') == 'example_remote_field'
        assert compat.get_remote_field(object(), default='default_value') == 'default_value'

    def test_set_rollback_for_transaction_in_managed_mode(self):
        class MockTransaction(object):
            called_rollback = False
            called_leave_transaction_management = False

            def is_managed(self):
                return True

            def is_dirty(self):
                return True

            def rollback(self):
                self.called_rollback = True

            def leave_transaction_management(self):
                self.called_leave_transaction_management = True

        dirty_mock_transaction = MockTransaction()
        compat.transaction = dirty_mock_transaction
        compat.set_rollback()
        assert dirty_mock_transaction.called_rollback is True
        assert dirty_mock_transaction.called_leave_transaction_management is True

        clean_mock_transaction = MockTransaction()
        clean_mock_transaction.is_dirty = lambda: False
        compat.transaction = clean_mock_transaction
        compat.set_rollback()
        assert clean_mock_transaction.called_rollback is False
        assert clean_mock_transaction.called_leave_transaction_management is True
