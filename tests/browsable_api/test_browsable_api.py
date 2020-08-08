from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from jinja2.exceptions import TemplateSyntaxError

from rest_framework.test import APIClient

from .multiple_template_engines import TEMPLATES


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


@override_settings(ROOT_URLCONF='tests.browsable_api.auth_urls')
@override_settings(TEMPLATES=TEMPLATES)
class CustomTemplateEngineTests(TestCase):
    """
    Within django multiple template engines can be configured.
    Some configurations will break the rest_framework used templates to render.
    Usually the first template engine that finds a template by name will be used.
    While using django_jinja2 and search extension configured to '*.html'
    all the django common tags like `load` won't work anymore.
    """

    def setUp(self):
        self.client = Client()

    def test_TemplateSyntaxError(self):
        with self.assertRaises(TemplateSyntaxError):
            self.client.get('/')

    def test_default_template_engine_setting(self):
        # FIXME: when I set this in rest_framework/settings.py
        # it's working...
        # no idea how to properly change this setting for this testcase?
        with override_settings(REST_FRAMEWORK={'DEFAULT_TEMPLATE_ENGINE': 'django'}):
            self.client.get('/')
