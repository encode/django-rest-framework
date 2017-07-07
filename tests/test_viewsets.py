from django.test import TestCase

from rest_framework import status
from rest_framework.response import Response
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


class InitializeViewSetsTestCase(TestCase):
    def test_initialize_view_set_with_actions(self):
        request = factory.get('/', '', content_type='application/json')
        my_view = BasicViewSet.as_view(actions={
            'get': 'list',
        })

        response = my_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {'ACTION': 'LIST'}

    def testhead_request_against_viewset(self):
        request = factory.head('/', '', content_type='application/json')
        my_view = BasicViewSet.as_view(actions={
            'get': 'list',
        })

        response = my_view(request)
        assert response.status_code == status.HTTP_200_OK

    def test_initialize_view_set_with_empty_actions(self):
        try:
            BasicViewSet.as_view()
        except TypeError as e:
            assert str(e) == ("The `actions` argument must be provided "
                              "when calling `.as_view()` on a ViewSet. "
                              "For example `.as_view({'get': 'list'})`")
        else:
            self.fail("actions must not be empty.")

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
