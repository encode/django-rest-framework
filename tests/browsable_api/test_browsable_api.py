from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from rest_framework import permissions, renderers, serializers, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.test import APIClient, APIRequestFactory
from tests.models import BasicModel

factory = APIRequestFactory()


class BasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = BasicModel
        fields = '__all__'


class OrganizationPermissions(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or (request.user == obj.owner.organization_user.user)


class StandardModelView(viewsets.ModelViewSet):
    queryset = BasicModel.objects.all()
    serializer_class = BasicSerializer
    permission_classes = [IsAuthenticated, OrganizationPermissions]
    renderer_classes = (renderers.BrowsableAPIRenderer, renderers.JSONRenderer)

    def get_queryset(self):
        qs = super().get_queryset().filter(users=self.request.user)
        return qs


@override_settings(ROOT_URLCONF='tests.browsable_api.auth_urls')
class AnonymousUserTests(TestCase):
    """Tests correct handling of anonymous user request on endpoints with IsAuthenticated permission class."""
    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

    def tearDown(self):
        self.client.logout()

    def test_factory_returns_403(self):
        view = StandardModelView.as_view({'get': 'list'})
        request = factory.get('/')
        response = view(request).render()
        self.assertTrue(response.status_code == 403, msg=response.status_code)


@override_settings(ROOT_URLCONF='tests.browsable_api.auth_urls')
class DropdownWithAuthTests(TestCase):
    """Tests correct dropdown behaviour with Auth views enabled."""
    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)
        self.username = 'john'
        self.email = 'lennon@thebeatles.com'
        self.password = 'password'
        self.user = User.objects.create_user(
            self.username,
            self.email,
            self.password
        )

    def tearDown(self):
        self.client.logout()

    def test_name_shown_when_logged_in(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get('/')
        content = response.content.decode('utf8')
        assert 'john' in content

    def test_logout_shown_when_logged_in(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get('/')
        content = response.content.decode('utf8')
        assert '>Log out<' in content

    def test_login_shown_when_logged_out(self):
        response = self.client.get('/')
        content = response.content.decode('utf8')
        assert '>Log in<' in content


@override_settings(ROOT_URLCONF='tests.browsable_api.no_auth_urls')
class NoDropdownWithoutAuthTests(TestCase):
    """Tests correct dropdown behaviour with Auth views NOT enabled."""
    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)
        self.username = 'john'
        self.email = 'lennon@thebeatles.com'
        self.password = 'password'
        self.user = User.objects.create_user(
            self.username,
            self.email,
            self.password
        )

    def tearDown(self):
        self.client.logout()

    def test_name_shown_when_logged_in(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get('/')
        content = response.content.decode('utf8')
        assert 'john' in content

    def test_dropdown_not_shown_when_logged_in(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get('/')
        content = response.content.decode('utf8')
        assert '<li class="dropdown">' not in content

    def test_dropdown_not_shown_when_logged_out(self):
        response = self.client.get('/')
        content = response.content.decode('utf8')
        assert '<li class="dropdown">' not in content
