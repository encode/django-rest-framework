from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import TestCase, override_settings
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver

from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.routers import SimpleRouter
from rest_framework.test import APIClient
from rest_framework.utils import json
from rest_framework.viewsets import ModelViewSet
from tests.models import BasicModel

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


class BasicModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = BasicModel
        fields = "__all__"


class ResourceViewSet(ModelViewSet):
    serializer_class = BasicModelSerializer
    queryset = BasicModel.objects.all()


router = SimpleRouter()
router.register(r'resources', ResourceViewSet)
router.register(r'resources-2', ResourceViewSet)
urlpatterns = []
urlpatterns += router.urls


@override_settings(ROOT_URLCONF='tests.browsable_api.test_browsable_api')
class SeleniumTests(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.selenium = WebDriver()
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def test_post_raw_data(self):
        self.selenium.get('%s%s' % (self.live_server_url, '/resources'))
        raw_tab = self.selenium.find_element(By.NAME, "raw-tab")
        raw_tab.click()

        # Raw data textarea is pre-populated with empty value.
        text_input = self.selenium.find_element(By.ID, "id__content")
        self.assertEqual(json.loads(text_input.text), {'text': ''})

        # Do submit and the data will be presisted then.
        text_input.clear()
        json_data = json.dumps({"text": "text description"}, indent=4)
        text_input.send_keys(json_data)
        post_button = self.selenium.find_element(By.CSS_SELECTOR, '#post-generic-content-form div.form-actions button')
        post_button.click()
        text_input = self.selenium.find_element(By.ID, "id__content")
        self.assertEqual(json.loads(text_input.text), {'text': 'text description'})
        self.assertEqual(BasicModel.objects.last().text, 'text description')

        # Moving to another resource view, the raw data will be clean.
        self.selenium.get('%s%s' % (self.live_server_url, '/resources-2'))
        text_input = self.selenium.find_element(By.ID, "id__content")
        self.assertEqual(json.loads(text_input.text), {'text': ''})

        # Do a second submit from the second view.
        text_input.clear()
        json_data = json.dumps({"text": "text description 2"}, indent=4)
        text_input.send_keys(json_data)
        post_button = self.selenium.find_element(By.CSS_SELECTOR, '#post-generic-content-form div.form-actions button')
        post_button.click()
        text_input = self.selenium.find_element(By.ID, "id__content")
        self.assertEqual(json.loads(text_input.text), {'text': 'text description 2'})
        self.assertEqual(BasicModel.objects.last().text, 'text description 2')

        # Do a third submit, from the same view, with the previous data
        # (which was pre-populated).
        post_button = self.selenium.find_element(By.CSS_SELECTOR, '#post-generic-content-form div.form-actions button')
        post_button.click()
        self.assertEqual(BasicModel.objects.count(), 3)
        self.assertEqual(BasicModel.objects.last().text, 'text description 2')

        # Only two keys were stored.
        session_storage_data = self.selenium.execute_script(
            'return JSON.parse(sessionStorage.getItem("rawDataSubmitted"))'
        )
        self.assertEqual(
            ['/resources-2/', '/resources/'],
            list(session_storage_data.keys())
        )
        self.assertEqual(
            ['{\n    "text": "text description 2"\n}', '{\n    "text": "text description"\n}'],
            list(session_storage_data.values())
        )
