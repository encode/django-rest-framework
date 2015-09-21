from django.test import TestCase

from rest_framework import db_routers, generics
from rest_framework.test import APIRequestFactory

from .models import BasicModel


class NoRoutersView(generics.GenericAPIView):
    db_router_classes = []
    queryset = BasicModel.objects.all()


class DjangoRouterView(generics.GenericAPIView):
    db_router_classes = [db_routers.DjangoDbRouter]
    queryset = BasicModel.objects.all()


class Router(object):
    def db_for_read(self, model, **hints):
        return 'db_for_read'

    def db_for_write(self, model, **hints):
        return 'db_for_write'


class BaseRoutersTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def assertViewUsesAliasForQuerySet(self, view_class, http_method, db_alias):
        with self.settings(DATABASE_ROUTERS=['tests.test_db_routers.Router']):
            request = getattr(self.factory, http_method)('/')
            view = view_class()
            view.request = request

            queryset = view.get_queryset()
            self.assertEqual(queryset._db, db_alias)


class TestNoDbRouters(BaseRoutersTest):
    def test_get(self):
        self.assertViewUsesAliasForQuerySet(NoRoutersView, http_method='get', db_alias=None)

    def test_post(self):
        self.assertViewUsesAliasForQuerySet(NoRoutersView, http_method='post', db_alias=None)

    def test_put(self):
        self.assertViewUsesAliasForQuerySet(NoRoutersView, http_method='put', db_alias=None)

    def test_patch(self):
        self.assertViewUsesAliasForQuerySet(NoRoutersView, http_method='patch', db_alias=None)


class TestDjangoDbRouter(BaseRoutersTest):
    def test_get(self):
        self.assertViewUsesAliasForQuerySet(DjangoRouterView, http_method='get', db_alias=None)

    def test_post(self):
        self.assertViewUsesAliasForQuerySet(DjangoRouterView, http_method='post', db_alias='db_for_write')

    def test_put(self):
        self.assertViewUsesAliasForQuerySet(DjangoRouterView, http_method='put', db_alias='db_for_write')

    def test_patch(self):
        self.assertViewUsesAliasForQuerySet(DjangoRouterView, http_method='patch', db_alias='db_for_write')
