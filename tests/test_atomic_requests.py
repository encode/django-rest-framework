from __future__ import unicode_literals

from django.db import connection, connections, transaction
from django.test import TestCase
from django.utils.unittest import skipUnless
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView
from tests.models import BasicModel


factory = APIRequestFactory()


class BasicView(APIView):
    def get(self, request, *args, **kwargs):
        BasicModel.objects.create()
        return Response({'method': 'GET'})


class ErrorView(APIView):
    def get(self, request, *args, **kwargs):
        BasicModel.objects.create()
        raise Exception


class APIExceptionView(APIView):
    def get(self, request, *args, **kwargs):
        BasicModel.objects.create()
        raise APIException


@skipUnless(connection.features.uses_savepoints,
            "'atomic' requires transactions and savepoints.")
class DBTransactionTests(TestCase):
    def setUp(self):
        self.view = BasicView.as_view()
        connections.databases['default']['ATOMIC_REQUESTS'] = True

    def tearDown(self):
        connections.databases['default']['ATOMIC_REQUESTS'] = False

    def test_no_exception_conmmit_transaction(self):
        request = factory.get('/')

        with self.assertNumQueries(1):
            response = self.view(request)
        self.assertFalse(transaction.get_rollback())
        self.assertEqual(response.status_code, status.HTTP_200_OK)


@skipUnless(connection.features.uses_savepoints,
            "'atomic' requires transactions and savepoints.")
class DBTransactionErrorTests(TestCase):
    def setUp(self):
        self.view = ErrorView.as_view()
        connections.databases['default']['ATOMIC_REQUESTS'] = True

    def tearDown(self):
        connections.databases['default']['ATOMIC_REQUESTS'] = False

    def test_error_rollback_transaction(self):
        """
        Transaction is eventually managed by outer-most transaction atomic
        block. DRF do not try to interfere here.
        """
        request = factory.get('/')
        with self.assertNumQueries(3):
            # 1 - begin savepoint
            # 2 - insert
            # 3 - release savepoint
            with transaction.atomic():
                self.assertRaises(Exception, self.view, request)
                self.assertFalse(transaction.get_rollback())


@skipUnless(connection.features.uses_savepoints,
            "'atomic' requires transactions and savepoints.")
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
        request = factory.get('/')
        num_queries = (4 if getattr(connection.features,
                                    'can_release_savepoints', False) else 3)
        with self.assertNumQueries(num_queries):
            # 1 - begin savepoint
            # 2 - insert
            # 3 - rollback savepoint
            # 4 - release savepoint (django>=1.8 only)
            with transaction.atomic():
                response = self.view(request)
                self.assertTrue(transaction.get_rollback())
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR)
