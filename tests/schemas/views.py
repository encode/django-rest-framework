from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework import serializers
from rest_framework.response import Response


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


class ExampleGenericViewSet(GenericViewSet):

    class ExampleSerializer(serializers.Serializer):
        date = serializers.DateField()
        datetime = serializers.DateTimeField()

    serializer_class = ExampleSerializer

    def get(self, *args, **kwargs):
        from datetime import datetime
        now = datetime.now()

        serializer = self.get_serializer(data=now.date(),datetime=now)
        return Response(serializer.data)