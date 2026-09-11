from django.test import TestCase, override_settings
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework.utils import json

from . import models, serializers


class TestSerializer(TestCase):
    def test_create(self):
        item = models.Item.objects.create(name='test')
        data = {
            "items": [
                {
                    "item": item.id,
                    "amount": 100,
                }
            ],
        }
        serializer = serializers.SummarySerializer(data=data)
        serializer.is_valid(raise_exception=True)
        expected_data = {
            "itemamount_set": [
                {
                    "item": item,
                    "amount": 100,
                }
            ],
        }
        assert serializer.validated_data == expected_data
        serializer.save()
        assert models.Summary.objects.count() == 1


@override_settings(ROOT_URLCONF='tests.issue.urls')
class TestIssueViewSet(TestCase):
    def test_create(self):
        api_client = APIClient()
        item = models.Item.objects.create(name='test')
        data = {
            "items": [
                {
                    "item": item.id,
                    "amount": 100,
                }
            ],
        }
        response = api_client.post(reverse('summary-list'), data)
        print(response.content)
        assert response.status_code == 201

    def test_create_with_json(self):
        api_client = APIClient()
        item = models.Item.objects.create(name='test')
        data = {
            "items": [
                {
                    "item": item.id,
                    "amount": 100,
                }
            ],
        }
        response = api_client.post(reverse('summary-list'), json.dumps(data), content_type='application/json')
        assert response.status_code == 201
