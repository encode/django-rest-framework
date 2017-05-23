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
        header_re = 'h{level}\s+id="{path}".*>\s*{title}\s*<a href="#{path}"'

        for route in (('not_dummies',), ('dummy', 'aaaas'), ('dummy', 'bbbbs')):
            path = "-".join(route)
            self.assertTrue(
                re.search(header_re.format(level=1+len(route), path=path, title=route[-1]), self.content),
                'unable to find documentation section for {}'.format(path)
            )
            for method in ('read', 'create'):
                subpath = "{}-retrieve_alt-{}".format(path, method)
                self.assertTrue(
                    re.search(header_re.format(level=3, path=subpath, title=method), self.content),
                    'unable to find documentation section for {}'.format(subpath)
                )
                action_code = 'action = [{}, "retrieve_alt", "{}"]'.format(
                    ", ".join('"{}"'.format(r) for r in route),
                    method
                )
                self.assertTrue(
                    action_code in self.content.replace('&quot;', '"'),
                    'unable to find code snippet for {}'.format(subpath)
                )
                self.assertTrue(
                    '$ coreapi action {} retrieve_alt {}'.format(' '.join(route), method) in self.content,
                    'unable to find shell code snippet for {}'.format(subpath)
                )
