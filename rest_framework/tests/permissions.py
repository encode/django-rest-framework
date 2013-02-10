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

        self.permitted_credentials = basic_auth_header('permitted', 'password')
        self.disallowed_credentials = basic_auth_header('disallowed', 'password')

        BasicModel(text='foo').save()

    def test_has_create_permissions(self):
        request = factory.post('/', json.dumps({'text': 'foobar'}),
                               content_type='application/json',
                               HTTP_AUTHORIZATION=self.permitted_credentials)
        response = root_view(request, pk=1)
        self.assertEquals(response.status_code, status.HTTP_201_CREATED)

    def test_has_put_permissions(self):
        request = factory.put('/1', json.dumps({'text': 'foobar'}),
                              content_type='application/json',
                              HTTP_AUTHORIZATION=self.permitted_credentials)
        response = instance_view(request, pk='1')
        self.assertEquals(response.status_code, status.HTTP_200_OK)

    def test_has_delete_permissions(self):
        request = factory.delete('/1', HTTP_AUTHORIZATION=self.permitted_credentials)
        response = instance_view(request, pk=1)
        self.assertEquals(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_does_not_have_create_permissions(self):
        request = factory.post('/', json.dumps({'text': 'foobar'}),
                               content_type='application/json',
                               HTTP_AUTHORIZATION=self.disallowed_credentials)
        response = root_view(request, pk=1)
        self.assertEquals(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_does_not_have_put_permissions(self):
        request = factory.put('/1', json.dumps({'text': 'foobar'}),
                              content_type='application/json',
                              HTTP_AUTHORIZATION=self.disallowed_credentials)
        response = instance_view(request, pk='1')
        self.assertEquals(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_does_not_have_delete_permissions(self):
        request = factory.delete('/1', HTTP_AUTHORIZATION=self.disallowed_credentials)
        response = instance_view(request, pk=1)
        self.assertEquals(response.status_code, status.HTTP_403_FORBIDDEN)
