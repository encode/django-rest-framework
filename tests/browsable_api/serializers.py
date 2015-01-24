from .models import Foo, Bar
from rest_framework.serializers import HyperlinkedModelSerializer, HyperlinkedIdentityField


class FooSerializer(HyperlinkedModelSerializer):
    bar = HyperlinkedIdentityField(view_name='bar-list')

    class Meta:
        model = Foo


class BarSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = Bar
