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
    queryset = User.objects.all().prefetch_related('groups')
    serializer_class = UserSerializer


class TestPrefetchRelatedUpdates(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='tom', email='tom@example.com')
        self.groups = [Group.objects.create(name='a'), Group.objects.create(name='b')]
        self.user.groups = self.groups
        self.user.save()

    def test_prefetch_related_updates(self):
        view = UserUpdate.as_view()
        pk = self.user.pk
        groups_pk = self.groups[0].pk
        request = factory.put('/', {'username': 'new', 'groups': [groups_pk]}, format='json')
        response = view(request, pk=pk)
        assert User.objects.get(pk=pk).groups.count() == 1
        expected = {
            'id': pk,
            'username': 'new',
            'groups': [1],
            'email': 'tom@example.com'
        }
        assert response.data == expected
