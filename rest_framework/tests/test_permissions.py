from __future__ import unicode_literals
from django.contrib.auth.models import User, Permission, Group
from django.db import models
from django.test import TestCase
from django.utils import unittest
from rest_framework import generics, status, permissions, authentication, HTTP_HEADER_ENCODING
from rest_framework.compat import guardian, get_model_name
from rest_framework.filters import DjangoObjectPermissionsFilter
from rest_framework.test import APIRequestFactory
from rest_framework.tests.models import BasicModel
import base64

factory = APIRequestFactory()

class RootView(generics.ListCreateAPIView):
    model = BasicModel
    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [permissions.DjangoModelPermissions]


class InstanceView(generics.RetrieveUpdateDestroyAPIView):
    model = BasicModel
    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [permissions.DjangoModelPermissions]

root_view = RootView.as_view()
instance_view = InstanceView.as_view()


def basic_auth_header(username, password):
    credentials = ('%s:%s' % (username, password))
    base64_credentials = base64.b64encode(credentials.encode(HTTP_HEADER_ENCODING)).decode(HTTP_HEADER_ENCODING)
    return 'Basic %s' % base64_credentials


class ModelPermissionsIntegrationTests(TestCase):
    def setUp(self):
        User.objects.create_user('disallowed', 'disallowed@example.com', 'password')
        user = User.objects.create_user('permitted', 'permitted@example.com', 'password')
        user.user_permissions = [
            Permission.objects.get(codename='add_basicmodel'),
            Permission.objects.get(codename='change_basicmodel'),
            Permission.objects.get(codename='delete_basicmodel')
        ]
        user = User.objects.create_user('updateonly', 'updateonly@example.com', 'password')
        user.user_permissions = [
            Permission.objects.get(codename='change_basicmodel'),
        ]

        self.permitted_credentials = basic_auth_header('permitted', 'password')
        self.disallowed_credentials = basic_auth_header('disallowed', 'password')
        self.updateonly_credentials = basic_auth_header('updateonly', 'password')

        BasicModel(text='foo').save()

    def test_has_create_permissions(self):
        request = factory.post('/', {'text': 'foobar'}, format='json',
                               HTTP_AUTHORIZATION=self.permitted_credentials)
        response = root_view(request, pk=1)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_has_put_permissions(self):
        request = factory.put('/1', {'text': 'foobar'}, format='json',
                              HTTP_AUTHORIZATION=self.permitted_credentials)
        response = instance_view(request, pk='1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_has_delete_permissions(self):
        request = factory.delete('/1', HTTP_AUTHORIZATION=self.permitted_credentials)
        response = instance_view(request, pk=1)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_does_not_have_create_permissions(self):
        request = factory.post('/', {'text': 'foobar'}, format='json',
                               HTTP_AUTHORIZATION=self.disallowed_credentials)
        response = root_view(request, pk=1)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_does_not_have_put_permissions(self):
        request = factory.put('/1', {'text': 'foobar'}, format='json',
                              HTTP_AUTHORIZATION=self.disallowed_credentials)
        response = instance_view(request, pk='1')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_does_not_have_delete_permissions(self):
        request = factory.delete('/1', HTTP_AUTHORIZATION=self.disallowed_credentials)
        response = instance_view(request, pk=1)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_has_put_as_create_permissions(self):
        # User only has update permissions - should be able to update an entity.
        request = factory.put('/1', {'text': 'foobar'}, format='json',
                              HTTP_AUTHORIZATION=self.updateonly_credentials)
        response = instance_view(request, pk='1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # But if PUTing to a new entity, permission should be denied.
        request = factory.put('/2', {'text': 'foobar'}, format='json',
                              HTTP_AUTHORIZATION=self.updateonly_credentials)
        response = instance_view(request, pk='2')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_options_permitted(self):
        request = factory.options('/',
                               HTTP_AUTHORIZATION=self.permitted_credentials)
        response = root_view(request, pk='1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('actions', response.data)
        self.assertEqual(list(response.data['actions'].keys()), ['POST'])

        request = factory.options('/1',
                               HTTP_AUTHORIZATION=self.permitted_credentials)
        response = instance_view(request, pk='1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('actions', response.data)
        self.assertEqual(list(response.data['actions'].keys()), ['PUT'])

    def test_options_disallowed(self):
        request = factory.options('/',
                               HTTP_AUTHORIZATION=self.disallowed_credentials)
        response = root_view(request, pk='1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('actions', response.data)

        request = factory.options('/1',
                               HTTP_AUTHORIZATION=self.disallowed_credentials)
        response = instance_view(request, pk='1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('actions', response.data)

    def test_options_updateonly(self):
        request = factory.options('/',
                               HTTP_AUTHORIZATION=self.updateonly_credentials)
        response = root_view(request, pk='1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('actions', response.data)

        request = factory.options('/1',
                               HTTP_AUTHORIZATION=self.updateonly_credentials)
        response = instance_view(request, pk='1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('actions', response.data)
        self.assertEqual(list(response.data['actions'].keys()), ['PUT'])


class BasicPermModel(models.Model):
    text = models.CharField(max_length=100)

    class Meta:
        app_label = 'tests'
        permissions = (
            ('view_basicpermmodel', 'Can view basic perm model'),
            # add, change, delete built in to django
        )

# Custom object-level permission, that includes 'view' permissions
class ViewObjectPermissions(permissions.DjangoObjectPermissions):
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': ['%(app_label)s.view_%(model_name)s'],
        'HEAD': ['%(app_label)s.view_%(model_name)s'],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }


class ObjectPermissionInstanceView(generics.RetrieveUpdateDestroyAPIView):
    model = BasicPermModel
    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [ViewObjectPermissions]

object_permissions_view = ObjectPermissionInstanceView.as_view()


class ObjectPermissionListView(generics.ListAPIView):
    model = BasicPermModel
    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [ViewObjectPermissions]

object_permissions_list_view = ObjectPermissionListView.as_view()


@unittest.skipUnless(guardian, 'django-guardian not installed')
class ObjectPermissionsIntegrationTests(TestCase):
    """
    Integration tests for the object level permissions API.
    """
    @classmethod
    def setUpClass(cls):
        from guardian.shortcuts import assign_perm

        # create users
        create = User.objects.create_user
        users = {
            'fullaccess': create('fullaccess', 'fullaccess@example.com', 'password'),
            'readonly': create('readonly', 'readonly@example.com', 'password'),
            'writeonly': create('writeonly', 'writeonly@example.com', 'password'),
            'deleteonly': create('deleteonly', 'deleteonly@example.com', 'password'),
        }

        # give everyone model level permissions, as we are not testing those
        everyone = Group.objects.create(name='everyone')
        model_name = get_model_name(BasicPermModel)
        app_label = BasicPermModel._meta.app_label
        f = '{0}_{1}'.format
        perms = {
            'view':   f('view', model_name),
            'change': f('change', model_name),
            'delete': f('delete', model_name)
        }
        for perm in perms.values():
            perm = '{0}.{1}'.format(app_label, perm)
            assign_perm(perm, everyone)
        everyone.user_set.add(*users.values())

        cls.perms = perms
        cls.users = users

    def setUp(self):
        from guardian.shortcuts import assign_perm
        perms = self.perms
        users = self.users

        # appropriate object level permissions
        readers = Group.objects.create(name='readers')
        writers = Group.objects.create(name='writers')
        deleters = Group.objects.create(name='deleters')

        model = BasicPermModel.objects.create(text='foo')
        
        assign_perm(perms['view'], readers, model)
        assign_perm(perms['change'], writers, model)
        assign_perm(perms['delete'], deleters, model)

        readers.user_set.add(users['fullaccess'], users['readonly'])
        writers.user_set.add(users['fullaccess'], users['writeonly'])
        deleters.user_set.add(users['fullaccess'], users['deleteonly'])

        self.credentials = {}
        for user in users.values():
            self.credentials[user.username] = basic_auth_header(user.username, 'password')

    # Delete
    def test_can_delete_permissions(self):
        request = factory.delete('/1', HTTP_AUTHORIZATION=self.credentials['deleteonly'])
        response = object_permissions_view(request, pk='1')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_cannot_delete_permissions(self):
        request = factory.delete('/1', HTTP_AUTHORIZATION=self.credentials['readonly'])
        response = object_permissions_view(request, pk='1')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # Update
    def test_can_update_permissions(self):
        request = factory.patch('/1', {'text': 'foobar'}, format='json',
            HTTP_AUTHORIZATION=self.credentials['writeonly'])
        response = object_permissions_view(request, pk='1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('text'), 'foobar')

    def test_cannot_update_permissions(self):
        request = factory.patch('/1', {'text': 'foobar'}, format='json',
            HTTP_AUTHORIZATION=self.credentials['deleteonly'])
        response = object_permissions_view(request, pk='1')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_update_permissions_non_existing(self):
        request = factory.patch('/999', {'text': 'foobar'}, format='json',
            HTTP_AUTHORIZATION=self.credentials['deleteonly'])
        response = object_permissions_view(request, pk='999')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # Read
    def test_can_read_permissions(self):
        request = factory.get('/1', HTTP_AUTHORIZATION=self.credentials['readonly'])
        response = object_permissions_view(request, pk='1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cannot_read_permissions(self):
        request = factory.get('/1', HTTP_AUTHORIZATION=self.credentials['writeonly'])
        response = object_permissions_view(request, pk='1')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # Read list
    def test_can_read_list_permissions(self):
        request = factory.get('/', HTTP_AUTHORIZATION=self.credentials['readonly'])
        object_permissions_list_view.cls.filter_backends = (DjangoObjectPermissionsFilter,)
        response = object_permissions_list_view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0].get('id'), 1)

    def test_cannot_read_list_permissions(self):
        request = factory.get('/', HTTP_AUTHORIZATION=self.credentials['writeonly'])
        object_permissions_list_view.cls.filter_backends = (DjangoObjectPermissionsFilter,)
        response = object_permissions_list_view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertListEqual(response.data, [])
