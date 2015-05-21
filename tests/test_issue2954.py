from django.db import models
from django.test import TestCase
from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework import viewsets
from rest_framework.test import APIRequestFactory
from rest_framework import status


factory = APIRequestFactory()


class TestInvalidModel(TestCase):

    def test_invalid_model(self):
        """
        """
        class InvalidModel(models.Model):
            afield = models.CharField(blank=True, max_length=10)

            def save(self, *args, **kwargs):
                # never save this object.
                raise ValidationError('a validation error')

        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = InvalidModel

        serializer = TestSerializer(data={'afield': 'foo'})
        serializer.is_valid()
        self.assertRaises(ValidationError, serializer.save)

        class TestModelViewSet(viewsets.ModelViewSet):
            serializer_class = TestSerializer
            queryset = InvalidModel.objects.all()

        request = factory.post('/', '{"afield": "foo"}', content_type='application/json')
        view = TestModelViewSet.as_view(actions={'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
