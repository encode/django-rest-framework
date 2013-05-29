from __future__ import unicode_literals
from django.contrib.auth.models import User, Permission
from django.db import models
from django.test import TestCase
from rest_framework import generics, status, permissions, authentication, HTTP_HEADER_ENCODING
from rest_framework.tests.utils import RequestFactory
import base64
import json

factory = RequestFactory()


class BasicModel(models.Model):
    text = models.CharField(max_length=100)


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
        request = factory.post('/', json.dumps({'text': 'foobar'}),
                               content_type='application/json',
                               HTTP_AUTHORIZATION=self.permitted_credentials)
        response = root_view(request, pk=1)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_has_put_permissions(self):
        request = factory.put('/1', json.dumps({'text': 'foobar'}),
                              content_type='application/json',
                              HTTP_AUTHORIZATION=self.permitted_credentials)
        response = instance_view(request, pk='1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_has_delete_permissions(self):
        request = factory.delete('/1', HTTP_AUTHORIZATION=self.permitted_credentials)
        response = instance_view(request, pk=1)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_does_not_have_create_permissions(self):
        request = factory.post('/', json.dumps({'text': 'foobar'}),
                               content_type='application/json',
                               HTTP_AUTHORIZATION=self.disallowed_credentials)
        response = root_view(request, pk=1)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_does_not_have_put_permissions(self):
        request = factory.put('/1', json.dumps({'text': 'foobar'}),
                              content_type='application/json',
                              HTTP_AUTHORIZATION=self.disallowed_credentials)
        response = instance_view(request, pk='1')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_does_not_have_delete_permissions(self):
        request = factory.delete('/1', HTTP_AUTHORIZATION=self.disallowed_credentials)
        response = instance_view(request, pk=1)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_has_put_as_create_permissions(self):
        # User only has update permissions - should be able to update an entity.
        request = factory.put('/1', json.dumps({'text': 'foobar'}),
                              content_type='application/json',
                              HTTP_AUTHORIZATION=self.updateonly_credentials)
        response = instance_view(request, pk='1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # But if PUTing to a new entity, permission should be denied.
        request = factory.put('/2', json.dumps({'text': 'foobar'}),
                              content_type='application/json',
                              HTTP_AUTHORIZATION=self.updateonly_credentials)
        response = instance_view(request, pk='2')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_options_permitted(self):
        request = factory.options('/', content_type='application/json',
                               HTTP_AUTHORIZATION=self.permitted_credentials)
        response = root_view(request, pk='1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('actions', response.data)
        self.assertEqual(list(response.data['actions'].keys()), ['POST'])

        request = factory.options('/1', content_type='application/json',
                               HTTP_AUTHORIZATION=self.permitted_credentials)
        response = instance_view(request, pk='1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('actions', response.data)
        self.assertEqual(list(response.data['actions'].keys()), ['PUT'])

    def test_options_disallowed(self):
        request = factory.options('/', content_type='application/json',
                               HTTP_AUTHORIZATION=self.disallowed_credentials)
        response = root_view(request, pk='1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('actions', response.data)

        request = factory.options('/1', content_type='application/json',
                               HTTP_AUTHORIZATION=self.disallowed_credentials)
        response = instance_view(request, pk='1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('actions', response.data)

    def test_options_updateonly(self):
        request = factory.options('/', content_type='application/json',
                               HTTP_AUTHORIZATION=self.updateonly_credentials)
        response = root_view(request, pk='1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('actions', response.data)

        request = factory.options('/1', content_type='application/json',
                               HTTP_AUTHORIZATION=self.updateonly_credentials)
        response = instance_view(request, pk='1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('actions', response.data)
        self.assertEqual(list(response.data['actions'].keys()), ['PUT'])


class OwnerModel(models.Model):
    text = models.CharField(max_length=100)
    owner = models.ForeignKey(User)


class IsOwnerPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user == obj.owner


class OwnerInstanceView(generics.RetrieveUpdateDestroyAPIView):
    model = OwnerModel
    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [IsOwnerPermission]


owner_instance_view = OwnerInstanceView.as_view()


class ObjectPermissionsIntegrationTests(TestCase):
    """
    Integration tests for the object level permissions API.
    """

    def setUp(self):
        User.objects.create_user('not_owner', 'not_owner@example.com', 'password')
        user = User.objects.create_user('owner', 'owner@example.com', 'password')

        self.not_owner_credentials = basic_auth_header('not_owner', 'password')
        self.owner_credentials = basic_auth_header('owner', 'password')

        OwnerModel(text='foo', owner=user).save()

    def test_owner_has_delete_permissions(self):
        request = factory.delete('/1', HTTP_AUTHORIZATION=self.owner_credentials)
        response = owner_instance_view(request, pk='1')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_non_owner_does_not_have_delete_permissions(self):
        request = factory.delete('/1', HTTP_AUTHORIZATION=self.not_owner_credentials)
        response = owner_instance_view(request, pk='1')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
