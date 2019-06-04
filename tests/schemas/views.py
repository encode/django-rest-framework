from rest_framework import generics, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet


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


# Generics.
class ExampleSerializer(serializers.Serializer):
    date = serializers.DateField()
    datetime = serializers.DateTimeField()


class ExampleGenericAPIView(generics.GenericAPIView):
    serializer_class = ExampleSerializer

    def get(self, *args, **kwargs):
        from datetime import datetime
        now = datetime.now()

        serializer = self.get_serializer(data=now.date(), datetime=now)
        return Response(serializer.data)


class ExampleGenericViewSet(GenericViewSet):
    serializer_class = ExampleSerializer

    def get(self, *args, **kwargs):
        from datetime import datetime
        now = datetime.now()

        serializer = self.get_serializer(data=now.date(), datetime=now)
        return Response(serializer.data)

    @action(detail=False)
    def new(self, *args, **kwargs):
        pass

    @action(detail=False)
    def old(self, *args, **kwargs):
        pass
