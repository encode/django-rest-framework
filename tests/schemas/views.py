from django.core.exceptions import PermissionDenied
from django.http import Http404

from rest_framework import filters, pagination, permissions, serializers
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

# Simple APIViews:


class ExampleListView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, *args, **kwargs):
        pass

    def post(self, request, *args, **kwargs):
        pass


class ExampleDetailView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, *args, **kwargs):
        pass


# Classes for ExampleViewSet

class ExamplePagination(pagination.PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'


class EmptySerializer(serializers.Serializer):
    pass


class ExampleSerializer(serializers.Serializer):
    a = serializers.CharField(required=True, help_text='A field description')
    b = serializers.CharField(required=False)
    read_only = serializers.CharField(read_only=True)
    hidden = serializers.HiddenField(default='hello')


class AnotherSerializerWithDictField(serializers.Serializer):
    a = serializers.DictField()


class AnotherSerializerWithListFields(serializers.Serializer):
    a = serializers.ListField(child=serializers.IntegerField())
    b = serializers.ListSerializer(child=serializers.CharField())


class AnotherSerializer(serializers.Serializer):
    c = serializers.CharField(required=True)
    d = serializers.CharField(required=False)


class ExampleViewSet(ModelViewSet):
    pagination_class = ExamplePagination
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    serializer_class = ExampleSerializer

    @action(methods=['post'], detail=True, serializer_class=AnotherSerializer)
    def custom_action(self, request, pk):
        """
        A description of custom action.
        """
        raise NotImplementedError

    @action(methods=['post'], detail=True, serializer_class=AnotherSerializerWithDictField)
    def custom_action_with_dict_field(self, request, pk):
        """
        A custom action using a dict field in the serializer.
        """
        raise NotImplementedError

    @action(methods=['post'], detail=True, serializer_class=AnotherSerializerWithListFields)
    def custom_action_with_list_fields(self, request, pk):
        """
        A custom action using both list field and list serializer in the serializer.
        """
        raise NotImplementedError

    @action(detail=False)
    def custom_list_action(self, request):
        raise NotImplementedError

    @action(methods=['post', 'get'], detail=False, serializer_class=EmptySerializer)
    def custom_list_action_multiple_methods(self, request):
        """Custom description."""
        raise NotImplementedError

    @custom_list_action_multiple_methods.mapping.delete
    def custom_list_action_multiple_methods_delete(self, request):
        """Deletion description."""
        raise NotImplementedError

    @action(detail=False, schema=None)
    def excluded_action(self, request):
        pass

    def get_serializer(self, *args, **kwargs):
        assert self.request
        assert self.action
        return super(ExampleViewSet, self).get_serializer(*args, **kwargs)


# ExampleViewSet subclasses

class DenyAllUsingHttp404(permissions.BasePermission):

    def has_permission(self, request, view):
        raise Http404()

    def has_object_permission(self, request, view, obj):
        raise Http404()


class DenyAllUsingPermissionDenied(permissions.BasePermission):

    def has_permission(self, request, view):
        raise PermissionDenied()

    def has_object_permission(self, request, view, obj):
        raise PermissionDenied()


class Http404ExampleViewSet(ExampleViewSet):
    permission_classes = [DenyAllUsingHttp404]


class PermissionDeniedExampleViewSet(ExampleViewSet):
    permission_classes = [DenyAllUsingPermissionDenied]


class MethodLimitedViewSet(ExampleViewSet):
    permission_classes = []
    http_method_names = ['get', 'head', 'options']
