from rest_framework.serializers import ModelSerializer
from tests.models import BasicModelWithUsers


class BasicSerializer(ModelSerializer):
    class Meta:
        model = BasicModelWithUsers
        fields = '__all__'
