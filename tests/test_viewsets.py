from collections import OrderedDict
from functools import wraps

import pytest
from django.db import models
from django.test import TestCase, override_settings
from django.urls import include, path

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.routers import SimpleRouter
from rest_framework.test import APIRequestFactory
from rest_framework.viewsets import GenericViewSet

factory = APIRequestFactory()


class BasicViewSet(GenericViewSet):
    def list(self, request, *args, **kwargs):
        return Response({'ACTION': 'LIST'})


class InstanceViewSet(GenericViewSet):

    def dispatch(self, request, *args, **kwargs):
        return self.dummy(request, *args, **kwargs)

    def dummy(self, request, *args, **kwargs):
        return Response({'view': self})


class Action(models.Model):
    pass


def decorate(fn):
    @wraps(fn)
    def wrapper(self, request, *args, **kwargs):
        return fn(self, request, *args, **kwargs)
    return wrapper


class ActionViewSet(GenericViewSet):
    queryset = Action.objects.all()

    def list(self, request, *args, **kwargs):
        response = Response()
        response.view = self
        return response

    def retrieve(self, request, *args, **kwargs):
        response = Response()
        response.view = self
        return response

    @action(detail=False)
    def list_action(self, request, *args, **kwargs):
        response = Response()
        response.view = self
        return response

    @action(detail=False, url_name='list-custom')
    def custom_list_action(self, request, *args, **kwargs):
        raise NotImplementedError

    @action(detail=True)
    def detail_action(self, request, *args, **kwargs):
        raise NotImplementedError

    @action(detail=True, url_name='detail-custom')
    def custom_detail_action(self, request, *args, **kwargs):
        raise NotImplementedError

    @action(detail=True, url_path=r'unresolvable/(?P<arg>\w+)', url_name='unresolvable')
    def unresolvable_detail_action(self, request, *args, **kwargs):
        raise NotImplementedError

    @action(detail=False)
    @decorate
    def wrapped_list_action(self, request, *args, **kwargs):
        raise NotImplementedError

    @action(detail=True)
    @decorate
    def wrapped_detail_action(self, request, *args, **kwargs):
        raise NotImplementedError


class ActionNamesViewSet(GenericViewSet):

    def retrieve(self, request, *args, **kwargs):
        response = Response()
        response.view = self
        return response

    @action(detail=True)
    def unnamed_action(self, request, *args, **kwargs):
        raise NotImplementedError

    @action(detail=True, name='Custom Name')
    def named_action(self, request, *args, **kwargs):
        raise NotImplementedError

    @action(detail=True, suffix='Custom Suffix')
    def suffixed_action(self, request, *args, **kwargs):
        raise NotImplementedError


class ThingWithMapping:
    def __init__(self):
        self.mapping = {}


class ActionViewSetWithMapping(ActionViewSet):
    mapper = ThingWithMapping()


router = SimpleRouter()
router.register(r'actions', ActionViewSet)
router.register(r'actions-alt', ActionViewSet, basename='actions-alt')
router.register(r'names', ActionNamesViewSet, basename='names')
router.register(r'mapping', ActionViewSetWithMapping, basename='mapping')


urlpatterns = [
    path('api/', include(router.urls)),
]


class InitializeViewSetsTestCase(TestCase):
    def test_initialize_view_set_with_actions(self):
        request = factory.get('/', '', content_type='application/json')
        my_view = BasicViewSet.as_view(actions={
            'get': 'list',
        })

        response = my_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {'ACTION': 'LIST'}

    def test_head_request_against_viewset(self):
        request = factory.head('/', '', content_type='application/json')
        my_view = BasicViewSet.as_view(actions={
            'get': 'list',
        })

        response = my_view(request)
        assert response.status_code == status.HTTP_200_OK

    def test_initialize_view_set_with_empty_actions(self):
        with pytest.raises(TypeError) as excinfo:
            BasicViewSet.as_view()

        assert str(excinfo.value) == (
            "The `actions` argument must be provided "
            "when calling `.as_view()` on a ViewSet. "
            "For example `.as_view({'get': 'list'})`")

    def test_initialize_view_set_with_both_name_and_suffix(self):
        with pytest.raises(TypeError) as excinfo:
            BasicViewSet.as_view(name='', suffix='', actions={
                'get': 'list',
            })

        assert str(excinfo.value) == (
            "BasicViewSet() received both `name` and `suffix`, "
            "which are mutually exclusive arguments.")

    def test_args_kwargs_request_action_map_on_self(self):
        """
        Test a view only has args, kwargs, request, action_map
        once `as_view` has been called.
        """
        bare_view = InstanceViewSet()
        view = InstanceViewSet.as_view(actions={
            'get': 'dummy',
        })(factory.get('/')).data['view']

        for attribute in ('args', 'kwargs', 'request', 'action_map'):
            self.assertNotIn(attribute, dir(bare_view))
            self.assertIn(attribute, dir(view))

    def test_viewset_action_attr(self):
        view = ActionViewSet.as_view(actions={'get': 'list'})

        get = view(factory.get('/'))
        head = view(factory.head('/'))
        assert get.view.action == 'list'
        assert head.view.action == 'list'

    def test_viewset_action_attr_for_extra_action(self):
        view = ActionViewSet.as_view(actions=dict(ActionViewSet.list_action.mapping))

        get = view(factory.get('/'))
        head = view(factory.head('/'))
        assert get.view.action == 'list_action'
        assert head.view.action == 'list_action'


class GetExtraActionsTests(TestCase):

    def test_extra_actions(self):
        view = ActionViewSet()
        actual = [action.__name__ for action in view.get_extra_actions()]
        expected = [
            'custom_detail_action',
            'custom_list_action',
            'detail_action',
            'list_action',
            'unresolvable_detail_action',
            'wrapped_detail_action',
            'wrapped_list_action',
        ]

        self.assertEqual(actual, expected)

    def test_should_only_return_decorated_methods(self):
        view = ActionViewSetWithMapping()
        actual = [action.__name__ for action in view.get_extra_actions()]
        expected = [
            'custom_detail_action',
            'custom_list_action',
            'detail_action',
            'list_action',
            'unresolvable_detail_action',
            'wrapped_detail_action',
            'wrapped_list_action',
        ]
        self.assertEqual(actual, expected)

    def test_attr_name_check(self):
        def decorate(fn):
            def wrapper(self, request, *args, **kwargs):
                return fn(self, request, *args, **kwargs)
            return wrapper

        class ActionViewSet(GenericViewSet):
            queryset = Action.objects.all()

            @action(detail=False)
            @decorate
            def wrapped_list_action(self, request, *args, **kwargs):
                raise NotImplementedError

        view = ActionViewSet()
        with pytest.raises(AssertionError) as excinfo:
            view.get_extra_actions()

        assert str(excinfo.value) == (
            'Expected function (`wrapper`) to match its attribute name '
            '(`wrapped_list_action`). If using a decorator, ensure the inner '
            'function is decorated with `functools.wraps`, or that '
            '`wrapper.__name__` is otherwise set to `wrapped_list_action`.')


@override_settings(ROOT_URLCONF='tests.test_viewsets')
class GetExtraActionUrlMapTests(TestCase):

    def test_list_view(self):
        response = self.client.get('/api/actions/')
        view = response.view

        expected = OrderedDict([
            ('Custom list action', 'http://testserver/api/actions/custom_list_action/'),
            ('List action', 'http://testserver/api/actions/list_action/'),
            ('Wrapped list action', 'http://testserver/api/actions/wrapped_list_action/'),
        ])

        self.assertEqual(view.get_extra_action_url_map(), expected)

    def test_detail_view(self):
        response = self.client.get('/api/actions/1/')
        view = response.view

        expected = OrderedDict([
            ('Custom detail action', 'http://testserver/api/actions/1/custom_detail_action/'),
            ('Detail action', 'http://testserver/api/actions/1/detail_action/'),
            ('Wrapped detail action', 'http://testserver/api/actions/1/wrapped_detail_action/'),
            # "Unresolvable detail action" excluded, since it's not resolvable
        ])

        self.assertEqual(view.get_extra_action_url_map(), expected)

    def test_uninitialized_view(self):
        self.assertEqual(ActionViewSet().get_extra_action_url_map(), OrderedDict())

    def test_action_names(self):
        # Action 'name' and 'suffix' kwargs should be respected
        response = self.client.get('/api/names/1/')
        view = response.view

        expected = OrderedDict([
            ('Custom Name', 'http://testserver/api/names/1/named_action/'),
            ('Action Names Custom Suffix', 'http://testserver/api/names/1/suffixed_action/'),
            ('Unnamed action', 'http://testserver/api/names/1/unnamed_action/'),
        ])

        self.assertEqual(view.get_extra_action_url_map(), expected)


@override_settings(ROOT_URLCONF='tests.test_viewsets')
class ReverseActionTests(TestCase):
    def test_default_basename(self):
        view = ActionViewSet()
        view.basename = router.get_default_basename(ActionViewSet)
        view.request = None

        assert view.reverse_action('list') == '/api/actions/'
        assert view.reverse_action('list-action') == '/api/actions/list_action/'
        assert view.reverse_action('list-custom') == '/api/actions/custom_list_action/'

        assert view.reverse_action('detail', args=['1']) == '/api/actions/1/'
        assert view.reverse_action('detail-action', args=['1']) == '/api/actions/1/detail_action/'
        assert view.reverse_action('detail-custom', args=['1']) == '/api/actions/1/custom_detail_action/'

    def test_custom_basename(self):
        view = ActionViewSet()
        view.basename = 'actions-alt'
        view.request = None

        assert view.reverse_action('list') == '/api/actions-alt/'
        assert view.reverse_action('list-action') == '/api/actions-alt/list_action/'
        assert view.reverse_action('list-custom') == '/api/actions-alt/custom_list_action/'

        assert view.reverse_action('detail', args=['1']) == '/api/actions-alt/1/'
        assert view.reverse_action('detail-action', args=['1']) == '/api/actions-alt/1/detail_action/'
        assert view.reverse_action('detail-custom', args=['1']) == '/api/actions-alt/1/custom_detail_action/'

    def test_request_passing(self):
        view = ActionViewSet()
        view.basename = router.get_default_basename(ActionViewSet)
        view.request = factory.get('/')

        # Passing the view's request object should result in an absolute URL.
        assert view.reverse_action('list') == 'http://testserver/api/actions/'

        # Users should be able to explicitly not pass the view's request.
        assert view.reverse_action('list', request=None) == '/api/actions/'
