from unittest import mock

from django.test import TestCase, override_settings
from django.urls import path

from rest_framework.decorators import action
from rest_framework.routers import SimpleRouter
from rest_framework.serializers import ModelSerializer
from rest_framework.utils import json
from rest_framework.utils.breadcrumbs import get_breadcrumbs
from rest_framework.utils.formatting import lazy_format
from rest_framework.utils.model_meta import FieldInfo, RelationInfo
from rest_framework.utils.urls import remove_query_param, replace_query_param
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from tests.models import BasicModel


class Root(APIView):
    pass


class ResourceRoot(APIView):
    pass


class ResourceInstance(APIView):
    pass


class NestedResourceRoot(APIView):
    pass


class NestedResourceInstance(APIView):
    pass


class CustomNameResourceInstance(APIView):
    def get_view_name(self):
        return "Foo"


class ResourceViewSet(ModelViewSet):
    serializer_class = ModelSerializer
    queryset = BasicModel.objects.all()

    @action(detail=False)
    def list_action(self, request, *args, **kwargs):
        raise NotImplementedError

    @action(detail=True)
    def detail_action(self, request, *args, **kwargs):
        raise NotImplementedError

    @action(detail=True, name='Custom Name')
    def named_action(self, request, *args, **kwargs):
        raise NotImplementedError

    @action(detail=True, suffix='Custom Suffix')
    def suffixed_action(self, request, *args, **kwargs):
        raise NotImplementedError


router = SimpleRouter()
router.register(r'resources', ResourceViewSet)
urlpatterns = [
    path('', Root.as_view()),
    path('resource/', ResourceRoot.as_view()),
    path('resource/customname', CustomNameResourceInstance.as_view()),
    path('resource/<int:key>', ResourceInstance.as_view()),
    path('resource/<int:key>/', NestedResourceRoot.as_view()),
    path('resource/<int:key>/<str:other>', NestedResourceInstance.as_view()),
]
urlpatterns += router.urls


@override_settings(ROOT_URLCONF='tests.test_utils')
class BreadcrumbTests(TestCase):
    """
    Tests the breadcrumb functionality used by the HTML renderer.
    """
    def test_root_breadcrumbs(self):
        url = '/'
        assert get_breadcrumbs(url) == [('Root', '/')]

    def test_resource_root_breadcrumbs(self):
        url = '/resource/'
        assert get_breadcrumbs(url) == [
            ('Root', '/'), ('Resource Root', '/resource/')
        ]

    def test_resource_instance_breadcrumbs(self):
        url = '/resource/123'
        assert get_breadcrumbs(url) == [
            ('Root', '/'),
            ('Resource Root', '/resource/'),
            ('Resource Instance', '/resource/123')
        ]

    def test_resource_instance_customname_breadcrumbs(self):
        url = '/resource/customname'
        assert get_breadcrumbs(url) == [
            ('Root', '/'),
            ('Resource Root', '/resource/'),
            ('Foo', '/resource/customname')
        ]

    def test_nested_resource_breadcrumbs(self):
        url = '/resource/123/'
        assert get_breadcrumbs(url) == [
            ('Root', '/'),
            ('Resource Root', '/resource/'),
            ('Resource Instance', '/resource/123'),
            ('Nested Resource Root', '/resource/123/')
        ]

    def test_nested_resource_instance_breadcrumbs(self):
        url = '/resource/123/abc'
        assert get_breadcrumbs(url) == [
            ('Root', '/'),
            ('Resource Root', '/resource/'),
            ('Resource Instance', '/resource/123'),
            ('Nested Resource Root', '/resource/123/'),
            ('Nested Resource Instance', '/resource/123/abc')
        ]

    def test_broken_url_breadcrumbs_handled_gracefully(self):
        url = '/foobar'
        assert get_breadcrumbs(url) == [('Root', '/')]

    def test_modelviewset_resource_instance_breadcrumbs(self):
        url = '/resources/1/'
        assert get_breadcrumbs(url) == [
            ('Root', '/'),
            ('Resource List', '/resources/'),
            ('Resource Instance', '/resources/1/')
        ]

    def test_modelviewset_list_action_breadcrumbs(self):
        url = '/resources/list_action/'
        assert get_breadcrumbs(url) == [
            ('Root', '/'),
            ('Resource List', '/resources/'),
            ('List action', '/resources/list_action/'),
        ]

    def test_modelviewset_detail_action_breadcrumbs(self):
        url = '/resources/1/detail_action/'
        assert get_breadcrumbs(url) == [
            ('Root', '/'),
            ('Resource List', '/resources/'),
            ('Resource Instance', '/resources/1/'),
            ('Detail action', '/resources/1/detail_action/'),
        ]

    def test_modelviewset_action_name_kwarg(self):
        url = '/resources/1/named_action/'
        assert get_breadcrumbs(url) == [
            ('Root', '/'),
            ('Resource List', '/resources/'),
            ('Resource Instance', '/resources/1/'),
            ('Custom Name', '/resources/1/named_action/'),
        ]

    def test_modelviewset_action_suffix_kwarg(self):
        url = '/resources/1/suffixed_action/'
        assert get_breadcrumbs(url) == [
            ('Root', '/'),
            ('Resource List', '/resources/'),
            ('Resource Instance', '/resources/1/'),
            ('Resource Custom Suffix', '/resources/1/suffixed_action/'),
        ]


class JsonFloatTests(TestCase):
    """
    Internally, wrapped json functions should adhere to strict float handling
    """

    def test_dumps(self):
        with self.assertRaises(ValueError):
            json.dumps(float('inf'))

        with self.assertRaises(ValueError):
            json.dumps(float('nan'))

    def test_loads(self):
        with self.assertRaises(ValueError):
            json.loads("Infinity")

        with self.assertRaises(ValueError):
            json.loads("NaN")


@override_settings(REST_FRAMEWORK={'STRICT_JSON': False})
class NonStrictJsonFloatTests(JsonFloatTests):
    """
    'STRICT_JSON = False' should not somehow affect internal json behavior
    """


class UrlsReplaceQueryParamTests(TestCase):
    """
    Tests the replace_query_param functionality.
    """
    def test_valid_unicode_preserved(self):
        # Encoded string: '查询'
        q = '/?q=%E6%9F%A5%E8%AF%A2'
        new_key = 'page'
        new_value = 2
        value = '%E6%9F%A5%E8%AF%A2'

        assert new_key in replace_query_param(q, new_key, new_value)
        assert value in replace_query_param(q, new_key, new_value)

    def test_valid_unicode_replaced(self):
        q = '/?page=1'
        value = '1'
        new_key = 'q'
        new_value = '%E6%9F%A5%E8%AF%A2'

        assert new_key in replace_query_param(q, new_key, new_value)
        assert value in replace_query_param(q, new_key, new_value)

    def test_invalid_unicode(self):
        # Encoded string: '��<script>alert(313)</script>=1'
        q = '/e/?%FF%FE%3C%73%63%72%69%70%74%3E%61%6C%65%72%74%28%33%31%33%29%3C%2F%73%63%72%69%70%74%3E=1'
        key = 'from'
        value = 'login'

        assert key in replace_query_param(q, key, value)


class UrlsRemoveQueryParamTests(TestCase):
    """
    Tests the remove_query_param functionality.
    """
    def test_valid_unicode_removed(self):
        q = '/?page=2345&q=%E6%9F%A5%E8%AF%A2'
        key = 'page'
        value = '2345'
        removed_key = 'q'

        assert key in remove_query_param(q, removed_key)
        assert value in remove_query_param(q, removed_key)
        assert '%' not in remove_query_param(q, removed_key)

    def test_invalid_unicode(self):
        q = '/?from=login&page=2&%FF%FE%3C%73%63%72%69%70%74%3E%61%6C%65%72%74%28%33%31%33%29%3C%2F%73%63%72%69%70%74%3E=1'
        key = 'from'
        removed_key = 'page'

        assert key in remove_query_param(q, removed_key)


class LazyFormatTests(TestCase):
    def test_it_formats_correctly(self):
        formatted = lazy_format('Does {} work? {answer}: %s', 'it', answer='Yes')
        assert str(formatted) == 'Does it work? Yes: %s'
        assert formatted % 'it does' == 'Does it work? Yes: it does'

    def test_it_formats_lazily(self):
        message = mock.Mock(wraps='message')
        formatted = lazy_format(message)
        assert message.format.call_count == 0
        str(formatted)
        assert message.format.call_count == 1
        str(formatted)
        assert message.format.call_count == 1


class ModelMetaNamedTupleNames(TestCase):
    def test_named_tuple_names(self):
        assert FieldInfo.__name__ == 'FieldInfo'
        assert RelationInfo.__name__ == 'RelationInfo'
