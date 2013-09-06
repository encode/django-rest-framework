from __future__ import unicode_literals
from django.contrib.auth.models import User, Permission
from django.db import models
from django.test import TestCase
from rest_framework import generics, status, permissions, authentication, HTTP_HEADER_ENCODING
from rest_framework.compat import guardian
from rest_framework.test import APIRequestFactory
from rest_framework.tests.models import BasicModel
from rest_framework.settings import api_settings
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


class BasicPermModel(BasicModel):

    class Meta:
        app_label = 'tests'
        permissions = (
            ('read_basicpermmodel', "Can view basic perm model"),
            # add, change, delete built in to django
        )

class ObjectPermissionInstanceView(generics.RetrieveUpdateDestroyAPIView):
    model = BasicModel
    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [permissions.DjangoObjectLevelModelPermissions]


object_permissions_view = ObjectPermissionInstanceView.as_view()

if guardian:
    class ObjectPermissionsIntegrationTests(TestCase):
        """
        Integration tests for the object level permissions API.
        """

        def setUp(self):
            # create users
            User.objects.create_user('no_permission', 'no_permission@example.com', 'password')
            reader = User.objects.create_user('reader', 'reader@example.com', 'password')
            writer = User.objects.create_user('writer', 'writer@example.com', 'password')
            full_access = User.objects.create_user('full_access', 'full_access@example.com', 'password')
            
            model = BasicPermModel.objects.create(text='foo')

            # assign permissions appropriately
            from guardian.shortcuts import assign_perm

            read = "read_basicpermmodel"
            write = "change_basicpermmodel"
            delete = "delete_basicpermmodel"
            app_label = 'tests.'
            # model level permissions
            assign_perm(app_label + delete, full_access, obj=model)
            (assign_perm(app_label + write, user, obj=model) for user in (writer, full_access))
            (assign_perm(app_label + read, user, obj=model) for user in (reader, writer, full_access))

            # object level permissions
            assign_perm(delete, full_access, obj=model)
            (assign_perm(write, user, obj=model) for user in (writer, full_access))
            (assign_perm(read, user, obj=model) for user in (reader, writer, full_access))

            self.no_permission_credentials = basic_auth_header('no_permission', 'password')
            self.reader_credentials = basic_auth_header('reader', 'password')
            self.writer_credentials = basic_auth_header('writer', 'password')
            self.full_access_credentials = basic_auth_header('full_access', 'password')


        def test_has_delete_permissions(self):
            request = factory.delete('/1', HTTP_AUTHORIZATION=self.full_access_credentials)
            response = object_permissions_view(request, pk='1')
            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        def test_no_delete_permissions(self):
            request = factory.delete('/1', HTTP_AUTHORIZATION=self.writer_credentials)
            response = object_permissions_view(request, pk='1')
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
