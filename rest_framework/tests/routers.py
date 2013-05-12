from __future__ import unicode_literals
from django.test import TestCase
from django.test.client import RequestFactory
from rest_framework import status
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.decorators import link, action
from rest_framework.routers import SimpleRouter
import copy

factory = RequestFactory()


class BasicViewSet(viewsets.ViewSet):
    def list(self, request, *args, **kwargs):
        return Response({'method': 'list'})

    @action()
    def action1(self, request, *args, **kwargs):
        return Response({'method': 'action1'})

    @action()
    def action2(self, request, *args, **kwargs):
        return Response({'method': 'action2'})

    @link()
    def link1(self, request, *args, **kwargs):
        return Response({'method': 'link1'})

    @link()
    def link2(self, request, *args, **kwargs):
        return Response({'method': 'link2'})


class TestSimpleRouter(TestCase):
    def setUp(self):
        self.router = SimpleRouter()

    def test_link_and_action_decorator(self):
        routes = self.router.get_routes(BasicViewSet)
        # Should be 2 by default, and then four from the @action and @link combined
        #self.assertEqual(len(routes), 6)
        #
        decorator_routes = routes[2:]
        for i, method in enumerate(['action1', 'action2', 'link1', 'link2']):
            self.assertEqual(decorator_routes[i].mapping.values()[0], method)
