import unittest

from django.db import connection, connections, transaction
from django.http import Http404
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import path

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView, set_rollback
from tests.models import BasicModel

factory = APIRequestFactory()


class BasicView(APIView):
    def post(self, request, *args, **kwargs):
        BasicModel.objects.create()
        return Response({'method': 'GET'})


class ErrorView(APIView):
    def post(self, request, *args, **kwargs):
        BasicModel.objects.create()
        raise Exception


class APIExceptionView(APIView):
    def post(self, request, *args, **kwargs):
        BasicModel.objects.create()
        raise APIException


class NonAtomicAPIExceptionView(APIView):
    @transaction.non_atomic_requests
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        BasicModel.objects.all()
        raise Http404


urlpatterns = (
    path('', NonAtomicAPIExceptionView.as_view()),
)


@unittest.skipUnless(
    connection.features.uses_savepoints,
    "'atomic' requires transactions and savepoints."
)
class DBTransactionTests(TestCase):
    def setUp(self):
        self.view = BasicView.as_view()
        connections.databases['default']['ATOMIC_REQUESTS'] = True

    def tearDown(self):
        connections.databases['default']['ATOMIC_REQUESTS'] = False

    def test_no_exception_commit_transaction(self):
        request = factory.post('/')

        with self.assertNumQueries(1):
            response = self.view(request)
        assert not transaction.get_rollback()
        assert response.status_code == status.HTTP_200_OK
        assert BasicModel.objects.count() == 1


@unittest.skipUnless(
    connection.features.uses_savepoints,
    "'atomic' requires transactions and savepoints."
)
class DBTransactionErrorTests(TestCase):
    def setUp(self):
        self.view = ErrorView.as_view()
        connections.databases['default']['ATOMIC_REQUESTS'] = True

    def tearDown(self):
        connections.databases['default']['ATOMIC_REQUESTS'] = False

    def test_generic_exception_delegate_transaction_management(self):
        """
        Transaction is eventually managed by outer-most transaction atomic
        block. DRF do not try to interfere here.

        We let django deal with the transaction when it will catch the Exception.
        """
        request = factory.post('/')
        with self.assertNumQueries(3):
            # 1 - begin savepoint
            # 2 - insert
            # 3 - release savepoint
            with transaction.atomic():
                self.assertRaises(Exception, self.view, request)
                assert not transaction.get_rollback()
        assert BasicModel.objects.count() == 1


@unittest.skipUnless(
    connection.features.uses_savepoints,
    "'atomic' requires transactions and savepoints."
)
class DBTransactionAPIExceptionTests(TestCase):
    def setUp(self):
        self.view = APIExceptionView.as_view()
        connections.databases['default']['ATOMIC_REQUESTS'] = True

    def tearDown(self):
        connections.databases['default']['ATOMIC_REQUESTS'] = False

    def test_api_exception_rollback_transaction(self):
        """
        Transaction is rollbacked by our transaction atomic block.
        """
        request = factory.post('/')
        num_queries = 4 if connection.features.can_release_savepoints else 3
        with self.assertNumQueries(num_queries):
            # 1 - begin savepoint
            # 2 - insert
            # 3 - rollback savepoint
            # 4 - release savepoint
            with transaction.atomic():
                response = self.view(request)
                assert transaction.get_rollback()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert BasicModel.objects.count() == 0


@unittest.skipUnless(
    connection.features.uses_savepoints,
    "'atomic' requires transactions and savepoints."
)
class MultiDBTransactionAPIExceptionTests(TestCase):
    databases = '__all__'

    def setUp(self):
        self.view = APIExceptionView.as_view()
        connections.databases['default']['ATOMIC_REQUESTS'] = True
        connections.databases['secondary']['ATOMIC_REQUESTS'] = True

    def tearDown(self):
        connections.databases['default']['ATOMIC_REQUESTS'] = False
        connections.databases['secondary']['ATOMIC_REQUESTS'] = False

    def test_api_exception_rollback_transaction(self):
        """
        Transaction is rollbacked by our transaction atomic block.
        """
        request = factory.post('/')
        num_queries = 4 if connection.features.can_release_savepoints else 3
        with self.assertNumQueries(num_queries):
            # 1 - begin savepoint
            # 2 - insert
            # 3 - rollback savepoint
            # 4 - release savepoint
            with transaction.atomic(), transaction.atomic(using='secondary'):
                response = self.view(request)
                assert transaction.get_rollback()
                assert transaction.get_rollback(using='secondary')
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert BasicModel.objects.count() == 0


@unittest.skipUnless(
    connection.features.uses_savepoints,
    "'atomic' requires transactions and savepoints."
)
@override_settings(ROOT_URLCONF='tests.test_atomic_requests')
class NonAtomicDBTransactionAPIExceptionTests(TransactionTestCase):
    def setUp(self):
        connections.databases['default']['ATOMIC_REQUESTS'] = True

    def tearDown(self):
        connections.databases['default']['ATOMIC_REQUESTS'] = False

    def test_api_exception_rollback_transaction_non_atomic_view(self):
        response = self.client.get('/')

        # without checking connection.in_atomic_block view raises 500
        # due attempt to rollback without transaction
        assert response.status_code == status.HTTP_404_NOT_FOUND


@unittest.skipUnless(
    connection.features.uses_savepoints,
    "'atomic' requires transactions and savepoints."
)
class SetRollbackTests(TestCase):
    def setUp(self):
        connections.databases['default']['ATOMIC_REQUESTS'] = True

    def tearDown(self):
        connections.databases['default']['ATOMIC_REQUESTS'] = False

    def test_marks_initialized_atomic_connection_for_rollback(self):
        with transaction.atomic():
            set_rollback()
            assert transaction.get_rollback()


class UninitializedSecondaryConnectionMixin:
    """
    Remove the 'secondary' connection wrapper from the current thread for
    the duration of a test, restoring the original wrapper afterwards so
    Django's test-case connection patching still finds it at class cleanup.
    """
    def setUp(self):
        super().setUp()
        self._saved_secondary = getattr(connections._connections, 'secondary', None)
        if self._saved_secondary is not None:
            delattr(connections._connections, 'secondary')

    def tearDown(self):
        stray = getattr(connections._connections, 'secondary', None)
        if stray is not None and stray is not self._saved_secondary:
            stray.close()
        if self._saved_secondary is not None:
            setattr(connections._connections, 'secondary', self._saved_secondary)
        super().tearDown()


class SetRollbackUninitializedConnectionTests(UninitializedSecondaryConnectionMixin, TestCase):
    def setUp(self):
        super().setUp()
        connections.databases['secondary']['ATOMIC_REQUESTS'] = True

    def tearDown(self):
        connections.databases['secondary']['ATOMIC_REQUESTS'] = False
        super().tearDown()

    def test_does_not_initialize_unused_connections(self):
        set_rollback()
        assert not hasattr(connections._connections, 'secondary')


class MultiDBUnusedConnectionAPIExceptionTests(UninitializedSecondaryConnectionMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.view = APIExceptionView.as_view()
        connections.databases['secondary']['ATOMIC_REQUESTS'] = True

    def tearDown(self):
        connections.databases['secondary']['ATOMIC_REQUESTS'] = False
        super().tearDown()

    def test_api_exception_leaves_unused_connection_uninitialized(self):
        request = factory.post('/')
        response = self.view(request)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert not hasattr(connections._connections, 'secondary')
