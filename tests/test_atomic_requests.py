import unittest
import warnings

from django.db import connection, connections, transaction
from django.http import Http404
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import path

from rest_framework import status
from rest_framework.deprecation import RemovedInDRF321Warning
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
        list(BasicModel.objects.all())
        raise Http404


urlpatterns = (
    path('non-atomic-exception', NonAtomicAPIExceptionView.as_view()),
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
                with self.assertRaises(Exception):
                    self.view(request)
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

        @self.addCleanup
        def restore_atomic_requests():
            connections.databases['default']['ATOMIC_REQUESTS'] = False

    def test_api_exception_rollback_transaction_non_atomic_view(self):
        response = self.client.get('/non-atomic-exception')

        # without check for db.in_atomic_block, would raise 500 due to attempt
        # to rollback without transaction
        assert response.status_code == status.HTTP_404_NOT_FOUND
        # Check we can still perform DB queries
        list(BasicModel.objects.all())


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
        request = factory.post('/')
        with transaction.atomic():
            set_rollback(request)
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
        request = factory.post('/')
        set_rollback(request)
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


@override_settings(ROOT_URLCONF='tests.test_atomic_requests')
class NonAtomicViewUnderTestCaseTests(TestCase):
    """
    Regression test for #6921.

    A view decorated with ``@transaction.non_atomic_requests`` must not
    poison the outer transaction that Django's ``TestCase`` wraps each
    test in. Before the fix, ``set_rollback`` would see
    ``connection.in_atomic_block == True`` and mark the outer transaction
    for rollback, breaking any subsequent queries in the test.
    """
    def setUp(self):
        connections.databases['default']['ATOMIC_REQUESTS'] = True

    def tearDown(self):
        connections.databases['default']['ATOMIC_REQUESTS'] = False

    def test_non_atomic_view_does_not_mark_outer_transaction_for_rollback(self):
        # TestCase has already opened an atomic block around this test.
        assert transaction.get_rollback() is False

        # Sending the request through the test client populates
        # ``request.resolver_match``, so ``set_rollback`` can see the
        # view's ``_non_atomic_requests`` attribute and skip the database.
        response = self.client.get('/')
        assert response.status_code == status.HTTP_404_NOT_FOUND

        # The outer transaction must remain usable. Without the fix,
        # ``set_rollback`` would have marked it for rollback and the
        # following query would raise.
        assert transaction.get_rollback() is False
        BasicModel.objects.create()


class SetRollbackDeprecationTests(TestCase):
    """
    Calling ``set_rollback()`` without a ``request`` argument should emit
    a ``RemovedInDRF321Warning``.
    """
    def test_calling_without_request_emits_warning(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            set_rollback()
        assert len(caught) == 1
        assert issubclass(caught[0].category, RemovedInDRF321Warning)
        assert "without a `request` argument is deprecated" in str(caught[0].message)


class SetRollbackWithoutResolverMatchTests(TestCase):
    """
    ``APIRequestFactory`` produces requests without a ``resolver_match``.
    ``set_rollback`` must fall back to the previous
    ``ATOMIC_REQUESTS + in_atomic_block`` behavior in that case.
    """
    def setUp(self):
        connections.databases['default']['ATOMIC_REQUESTS'] = True

    def tearDown(self):
        connections.databases['default']['ATOMIC_REQUESTS'] = False

    def test_falls_back_when_resolver_match_missing(self):
        request = factory.post('/')
        assert getattr(request, 'resolver_match', None) is None
        with transaction.atomic():
            set_rollback(request)
            assert transaction.get_rollback()
