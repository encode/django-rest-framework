from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from rest_framework.permissions import IsAuthenticated
from rest_framework.test import APIClient

from .views import BasicModelWithUsersViewSet, OrganizationPermissions


@override_settings(ROOT_URLCONF='tests.browsable_api.no_auth_urls')
class AnonymousUserTests(TestCase):
    """Tests correct handling of anonymous user request on endpoints with IsAuthenticated permission class."""

    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

    def tearDown(self):
        self.client.logout()

    def test_get_raises_typeerror_when_anonymous_user_in_queryset_filter(self):
        with self.assertRaises(TypeError):
            self.client.get('/basicviewset')

    def test_get_returns_http_forbidden_when_anonymous_user(self):
        old_permissions = BasicModelWithUsersViewSet.permission_classes
        BasicModelWithUsersViewSet.permission_classes = [IsAuthenticated, OrganizationPermissions]

        response = self.client.get('/basicviewset')

        BasicModelWithUsersViewSet.permission_classes = old_permissions
        self.assertEqual(response.status_code, 403)


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
        content = response.content.decode()
        assert 'john' in content

    def test_logout_shown_when_logged_in(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get('/')
        content = response.content.decode()
        assert '>Log out<' in content

    def test_login_shown_when_logged_out(self):
        response = self.client.get('/')
        content = response.content.decode()
        assert '>Log in<' in content

    def test_dropdown_contains_logout_form(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get('/')
        content = response.content.decode()
        assert '<form id="logoutForm" method="post" action="/auth/logout/?next=/">' in content


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
        content = response.content.decode()
        assert 'john' in content

    def test_dropdown_not_shown_when_logged_in(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get('/')
        content = response.content.decode()
        assert '<li class="dropdown">' not in content

    def test_dropdown_not_shown_when_logged_out(self):
        response = self.client.get('/')
        content = response.content.decode()
        assert '<li class="dropdown">' not in content
