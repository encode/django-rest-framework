from __future__ import unicode_literals

from rest_framework import authentication, renderers
from rest_framework.response import Response
from rest_framework.views import APIView


class MockView(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    renderer_classes = (renderers.BrowsableAPIRenderer, renderers.JSONRenderer)

    def get(self, request):
        return Response({'a': 1, 'b': 2, 'c': 3})
