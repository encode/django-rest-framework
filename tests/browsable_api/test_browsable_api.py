from __future__ import unicode_literals
from django.contrib.auth.models import User
from django.test import TestCase

from rest_framework.test import APIClient


class DropdownWithAuthTests(TestCase):
    """Tests correct dropdown behaviour with Auth views enabled."""

    urls = 'tests.browsable_api.auth_urls'

    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)
        self.username = 'john'
        self.email = 'lennon@thebeatles.com'
        self.password = 'password'
        self.user = User.objects.create_user(self.username, self.email, self.password)

    def tearDown(self):
        self.client.logout()

    def test_name_shown_when_logged_in(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get('/')
        self.assertContains(response, 'john')

    def test_logout_shown_when_logged_in(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get('/')
        self.assertContains(response, '>Log out<')

    def test_login_shown_when_logged_out(self):
        response = self.client.get('/')
        self.assertContains(response, '>Log in<')


class NoDropdownWithoutAuthTests(TestCase):
    """Tests correct dropdown behaviour with Auth views NOT enabled."""

    urls = 'tests.browsable_api.no_auth_urls'

    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)
        self.username = 'john'
        self.email = 'lennon@thebeatles.com'
        self.password = 'password'
        self.user = User.objects.create_user(self.username, self.email, self.password)

    def tearDown(self):
        self.client.logout()

    def test_name_shown_when_logged_in(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get('/')
        self.assertContains(response, 'john')

    def test_dropdown_not_shown_when_logged_in(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get('/')
        self.assertNotContains(response, '<li class="dropdown">')

    def test_dropdown_not_shown_when_logged_out(self):
        response = self.client.get('/')
        self.assertNotContains(response, '<li class="dropdown">')
