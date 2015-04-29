from __future__ import unicode_literals

from rest_framework_3.views import APIView
from rest_framework_3 import authentication
from rest_framework_3 import renderers
from rest_framework_3.response import Response


class MockView(APIView):

    authentication_classes = (authentication.SessionAuthentication,)
    renderer_classes = (renderers.BrowsableAPIRenderer,)

    def get(self, request):
        return Response({'a': 1, 'b': 2, 'c': 3})
