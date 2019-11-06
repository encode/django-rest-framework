import uuid

from django.core.validators import (
    DecimalValidator, MaxLengthValidator, MaxValueValidator,
    MinLengthValidator, MinValueValidator, RegexValidator
)

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


class DocStringExampleListView(APIView):
    """
    get: A description of my GET operation.
    post: A description of my POST operation.
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, *args, **kwargs):
        pass

    def post(self, request, *args, **kwargs):
        pass


class DocStringExampleDetailView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, *args, **kwargs):
        """
        A description of my GET operation.
        """
        pass


# Generics.
class ExampleSerializer(serializers.Serializer):
    date = serializers.DateField()
    datetime = serializers.DateTimeField()
    hstore = serializers.HStoreField()


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


# Validators and/or equivalent Field attributes.
class ExampleValidatedSerializer(serializers.Serializer):
    integer = serializers.IntegerField(
        validators=(
            MaxValueValidator(limit_value=99),
            MinValueValidator(limit_value=-11),
        )
    )
    string = serializers.CharField(
        validators=(
            MaxLengthValidator(limit_value=10),
            MinLengthValidator(limit_value=2),
        )
    )
    regex = serializers.CharField(
        validators=(
            RegexValidator(regex=r'[ABC]12{3}'),
        ),
        help_text='must have an A, B, or C followed by 1222'
    )
    lst = serializers.ListField(
        validators=(
            MaxLengthValidator(limit_value=10),
            MinLengthValidator(limit_value=2),
        )
    )
    decimal1 = serializers.DecimalField(max_digits=6, decimal_places=2)
    decimal2 = serializers.DecimalField(max_digits=5, decimal_places=0,
                                        validators=(DecimalValidator(max_digits=17, decimal_places=4),))
    email = serializers.EmailField(default='foo@bar.com')
    url = serializers.URLField(default='http://www.example.com', allow_null=True)
    uuid = serializers.UUIDField()
    ip4 = serializers.IPAddressField(protocol='ipv4')
    ip6 = serializers.IPAddressField(protocol='ipv6')
    ip = serializers.IPAddressField()


class ExampleValidatedAPIView(generics.GenericAPIView):
    serializer_class = ExampleValidatedSerializer

    def get(self, *args, **kwargs):
        serializer = self.get_serializer(integer=33, string='hello', regex='foo', decimal1=3.55,
                                         decimal2=5.33, email='a@b.co',
                                         url='http://localhost', uuid=uuid.uuid4(), ip4='127.0.0.1', ip6='::1',
                                         ip='192.168.1.1')
        return Response(serializer.data)
