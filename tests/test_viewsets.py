from django.test import TestCase

from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory
from rest_framework.viewsets import GenericViewSet

factory = APIRequestFactory()


class BasicViewSet(GenericViewSet):
    def list(self, request, *args, **kwargs):
        return Response({'ACTION': 'LIST'})


class InitializeViewSetsTestCase(TestCase):
    def test_initialize_view_set_with_actions(self):
        request = factory.get('/', '', content_type='application/json')
        my_view = BasicViewSet.as_view(actions={
            'get': 'list',
        })

        response = my_view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {'ACTION': 'LIST'}

    def test_initialize_view_set_with_empty_actions(self):
        try:
            BasicViewSet.as_view()
        except TypeError as e:
            assert str(e) == ("The `actions` argument must be provided "
                              "when calling `.as_view()` on a ViewSet. "
                              "For example `.as_view({'get': 'list'})`")
        else:
            self.fail("actions must not be empty.")
