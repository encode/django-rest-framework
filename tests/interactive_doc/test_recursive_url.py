from __future__ import unicode_literals

import re

from django.test import TestCase, override_settings

from rest_framework.test import APIClient


@override_settings(ROOT_URLCONF='tests.interactive_doc.urls')
class TestRecursiveUrlViewSets(TestCase):

    def setUp(self):
        client = APIClient()
        response = client.get('/docs/')
        self.content = response.content.decode('utf-8')

    def test_menu(self):
        self.assertTrue(
            re.search('a href="#.*not_dummies\-list">', self.content),
            'unable to find menu item for not_dummies'
        )
        for model_type in ['aaaa', 'bbbb']:
            self.assertTrue(
                re.search('a href="#.*{}s\-list">'.format(model_type), self.content),
                'unable to find menu item for dummy/{}'.format(model_type)
            )

    def test_documentation(self):
        self.assertTrue(
            re.search('h2.*>not_dummies <a', self.content),
            'unable to find documentation section for not_dummies'
        )
        for model_type in ['aaaa', 'bbbb']:
            self.assertTrue(
                re.search('h3.*>{}s <a'.format(model_type), self.content),
                'unable to find documentation section for dummy/{}'.format(model_type)
            )
