from django.contrib.auth.models import Group, User
from django.test import TestCase

from rest_framework import generics, serializers
from rest_framework.test import APIRequestFactory

factory = APIRequestFactory()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'groups')


class UserUpdate(generics.UpdateAPIView):
    queryset = User.objects.exclude(username='exclude')
    serializer_class = UserSerializer
    prefetch_related = ['groups']


class TestPrefetchRelatedUpdates(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='tom', email='tom@example.com')
        self.groups = [Group.objects.create(name='a'), Group.objects.create(name='b')]
        self.user.groups.set(self.groups)
        self.expected = {
            'id': self.user.pk,
            'username': 'new',
            'groups': [1],
            'email': 'tom@example.com',
        }
        self.view = UserUpdate.as_view()

    def test_prefetch_related_updates(self):
        request = factory.put(
            '/', {'username': 'new', 'groups': [self.groups[0].pk]}, format='json'
        )
        response = self.view(request, pk=self.user.pk)
        assert User.objects.get(pk=self.user.pk).groups.count() == 1
        assert response.data == self.expected

    def test_prefetch_related_excluding_instance_from_original_queryset(self):
        """
        Regression test for https://github.com/encode/django-rest-framework/issues/4661
        """
        request = factory.put(
            '/', {'username': 'exclude', 'groups': [self.groups[0].pk]}, format='json'
        )
        response = self.view(request, pk=self.user.pk)
        assert User.objects.get(pk=self.user.pk).groups.count() == 1
        self.expected['username'] = 'exclude'
        assert response.data == self.expected
