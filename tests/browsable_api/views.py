from rest_framework import authentication, renderers
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from ..models import BasicModelWithUsers
from .serializers import BasicSerializer


class OrganizationPermissions(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or (request.user == obj.owner.organization_user.user)


class MockView(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    renderer_classes = (renderers.BrowsableAPIRenderer, renderers.JSONRenderer)

    def get(self, request):
        return Response({'a': 1, 'b': 2, 'c': 3})


class BasicModelWithUsersViewSet(ModelViewSet):
    queryset = BasicModelWithUsers.objects.all()
    serializer_class = BasicSerializer
    permission_classes = [OrganizationPermissions]
    # permission_classes = [IsAuthenticated, OrganizationPermissions]
    renderer_classes = (renderers.BrowsableAPIRenderer, renderers.JSONRenderer)

    def get_queryset(self):
        qs = super().get_queryset().filter(users=self.request.user)
        return qs
