from django.test import TestCase

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.routers import DefaultRouter
from rest_framework.schemas.openapi import AutoSchema, SchemaGenerator
from rest_framework.serializers import Serializer
from rest_framework.viewsets import GenericViewSet


class TestViewInspectorDescriptor(TestCase):
    """
    Regression tests for #6877: a `ViewInspector` (e.g. `AutoSchema`)
    instance shared across multiple views, such as one assigned via
    `@action(schema=AutoSchema())` on a method defined in a mixin, must
    not leak the `view` it was last accessed with onto other views.
    """
    def test_schema_shared_via_mixin_action_is_not_shared_between_viewsets(self):
        shared_schema = AutoSchema()

        class CancelViewSetMixin:
            @action(methods=['post'], detail=True, schema=shared_schema)
            def cancel(self, request, pk):
                return Response()

        class ASerializer(Serializer):
            pass

        class BSerializer(Serializer):
            pass

        class ViewSetA(CancelViewSetMixin, GenericViewSet):
            serializer_class = ASerializer

        class ViewSetB(CancelViewSetMixin, GenericViewSet):
            serializer_class = BSerializer

        router = DefaultRouter()
        router.register(r'view-set-a', ViewSetA, basename='viewseta')
        router.register(r'view-set-b', ViewSetB, basename='viewsetb')

        generator = SchemaGenerator(title='Test', patterns=router.urls)
        schema = generator.get_schema(request=None, public=True)

        operation_id_a = schema['paths']['/view-set-a/{id}/cancel/']['post']['operationId']
        operation_id_b = schema['paths']['/view-set-b/{id}/cancel/']['post']['operationId']

        assert operation_id_a == 'cancelA'
        assert operation_id_b == 'cancelB'
