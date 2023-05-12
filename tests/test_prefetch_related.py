from django.contrib.auth.models import Group, User
from django.db.models.query import Prefetch
from django.test import TestCase

from rest_framework import generics, serializers
from rest_framework.test import APIRequestFactory

factory = APIRequestFactory()


class UserSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()

    def get_permissions(self, obj):
        ret = []
        for g in obj.groups.all():
            ret.extend([p.pk for p in g.permissions.all()])
        return ret

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'groups', 'permissions')


class UserRetrieveUpdate(generics.RetrieveUpdateAPIView):
    queryset = User.objects.exclude(username='exclude').prefetch_related(
        Prefetch('groups', queryset=Group.objects.exclude(name='exclude')),
        'groups__permissions',
    )
    serializer_class = UserSerializer


class UserUpdateWithoutPrefetchRelated(generics.UpdateAPIView):
    queryset = User.objects.exclude(username='exclude')
    serializer_class = UserSerializer


class TestPrefetchRelatedUpdates(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='tom', email='tom@example.com')
        self.groups = [Group.objects.create(name=f'group {i}') for i in range(10)]
        self.user.groups.set(self.groups)
        self.user.groups.add(Group.objects.create(name='exclude'))
        self.expected = {
            'id': self.user.pk,
            'username': 'tom',
            'groups': [group.pk for group in self.groups],
            'email': 'tom@example.com',
            'permissions': [],
        }
        self.view = UserRetrieveUpdate.as_view()

    def test_prefetch_related_updates(self):
        self.groups.append(Group.objects.create(name='c'))
        request = factory.put(
            '/', {'username': 'new', 'groups': [group.pk for group in self.groups]}, format='json'
        )
        self.expected['username'] = 'new'
        self.expected['groups'] = [group.pk for group in self.groups]
        response = self.view(request, pk=self.user.pk)
        assert User.objects.get(pk=self.user.pk).groups.count() == 12
        assert response.data == self.expected
        # Update and fetch should get same result
        request = factory.get('/')
        response = self.view(request, pk=self.user.pk)
        assert response.data == self.expected

    def test_prefetch_related_excluding_instance_from_original_queryset(self):
        """
        Regression test for https://github.com/encode/django-rest-framework/issues/4661
        """
        request = factory.put(
            '/', {'username': 'exclude', 'groups': [self.groups[0].pk]}, format='json'
        )
        response = self.view(request, pk=self.user.pk)
        assert User.objects.get(pk=self.user.pk).groups.count() == 2
        self.expected['username'] = 'exclude'
        self.expected['groups'] = [self.groups[0].pk]
        assert response.data == self.expected

    def test_db_query_count(self):
        request = factory.put(
            '/', {'username': 'new'}, format='json'
        )
        with self.assertNumQueries(7):
            self.view(request, pk=self.user.pk)

        request = factory.put(
            '/', {'username': 'new2'}, format='json'
        )
        with self.assertNumQueries(16):
            UserUpdateWithoutPrefetchRelated.as_view()(request, pk=self.user.pk)
