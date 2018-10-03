import unittest

import pytest
from django.conf.urls import url
from django.test import TestCase

from rest_framework.compat import coreapi, get_regex_pattern
from rest_framework.decorators import api_view, schema
from rest_framework.schemas.generators import (
    EndpointEnumerator, SchemaGenerator
)
from rest_framework.views import APIView


class EndpointExclusionTests(TestCase):
    class ExcludedAPIView(APIView):
        schema = None

        def get(self, request, *args, **kwargs):
            pass

    @api_view(['GET'])
    @schema(None)
    def excluded_fbv(request):
        pass

    @api_view(['GET'])
    def included_fbv(request):
        pass

    def setUp(self):
        self.patterns = [
            url('^excluded-cbv/$', self.ExcludedAPIView.as_view()),
            url('^excluded-fbv/$', self.excluded_fbv),
            url('^included-fbv/$', self.included_fbv),
        ]

    @unittest.skipUnless(coreapi, 'coreapi is not installed')
    def test_schema_generator_excludes_correctly(self):
        """Schema should not include excluded views"""
        generator = SchemaGenerator(title='Exclusions', patterns=self.patterns)
        schema = generator.get_schema()
        expected = coreapi.Document(
            url='',
            title='Exclusions',
            content={
                'included-fbv': {
                    'list': coreapi.Link(url='/included-fbv/', action='get')
                }
            }
        )

        assert len(schema.data) == 1
        assert 'included-fbv' in schema.data
        assert schema == expected

    def test_endpoint_enumerator_excludes_correctly(self):
        """It is responsibility of EndpointEnumerator to exclude views"""
        inspector = EndpointEnumerator(self.patterns)
        endpoints = inspector.get_api_endpoints()

        assert len(endpoints) == 1
        path, method, callback = endpoints[0]
        assert path == '/included-fbv/'

    def test_should_include_endpoint_excludes_correctly(self):
        """This is the specific method that should handle the exclusion"""
        inspector = EndpointEnumerator(self.patterns)

        # Not pretty. Mimics internals of EndpointEnumerator to put should_include_endpoint under test
        pairs = [(inspector.get_path_from_regex(get_regex_pattern(pattern)), pattern.callback)
                 for pattern in self.patterns]

        should_include = [
            inspector.should_include_endpoint(*pair) for pair in pairs
        ]

        expected = [False, False, True]

        assert should_include == expected

    def test_deprecations(self):
        with pytest.warns(DeprecationWarning) as record:
            @api_view(["GET"], exclude_from_schema=True)
            def view(request):
                pass

        assert len(record) == 1
        assert str(record[0].message) == (
            "The `exclude_from_schema` argument to `api_view` is deprecated. "
            "Use the `schema` decorator instead, passing `None`."
        )

        class OldFashionedExcludedView(APIView):
            exclude_from_schema = True

            def get(self, request, *args, **kwargs):
                pass

        patterns = [
            url('^excluded-old-fashioned/$', OldFashionedExcludedView.as_view()),
        ]

        inspector = EndpointEnumerator(patterns)
        with pytest.warns(DeprecationWarning) as record:
            inspector.get_api_endpoints()

        assert len(record) == 1
        assert str(record[0].message) == (
            "The `OldFashionedExcludedView.exclude_from_schema` attribute is "
            "deprecated. Set `schema = None` instead."
        )
