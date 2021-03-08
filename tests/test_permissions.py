import base64
import unittest
from unittest import mock

from django.conf import settings
from django.contrib.auth.models import AnonymousUser, Group, Permission, User
from django.db import models
from django.test import TestCase
from django.urls import ResolverMatch

from rest_framework import (
    HTTP_HEADER_ENCODING, authentication, generics, permissions, serializers,
    status, views
)
from rest_framework.routers import DefaultRouter
from rest_framework.test import APIRequestFactory
from tests.models import BasicModel

factory = APIRequestFactory()


class BasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = BasicModel
        fields = '__all__'


class RootView(generics.ListCreateAPIView):
    queryset = BasicModel.objects.all()
    serializer_class = BasicSerializer
    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [permissions.DjangoModelPermissions]


class InstanceView(generics.RetrieveUpdateDestroyAPIView):
    queryset = BasicModel.objects.all()
    serializer_class = BasicSerializer
    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [permissions.DjangoModelPermissions]


class GetQuerySetListView(generics.ListCreateAPIView):
    serializer_class = BasicSerializer
    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [permissions.DjangoModelPermissions]

    def get_queryset(self):
        return BasicModel.objects.all()


class EmptyListView(generics.ListCreateAPIView):
    queryset = BasicModel.objects.none()
    serializer_class = BasicSerializer
    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [permissions.DjangoModelPermissions]


root_view = RootView.as_view()
api_root_view = DefaultRouter().get_api_root_view()
instance_view = InstanceView.as_view()
get_queryset_list_view = GetQuerySetListView.as_view()
empty_list_view = EmptyListView.as_view()


def basic_auth_header(username, password):
    credentials = ('%s:%s' % (username, password))
    base64_credentials = base64.b64encode(credentials.encode(HTTP_HEADER_ENCODING)).decode(HTTP_HEADER_ENCODING)
    return 'Basic %s' % base64_credentials


class ModelPermissionsIntegrationTests(TestCase):
    def setUp(self):
        User.objects.create_user('disallowed', 'disallowed@example.com', 'password')
        user = User.objects.create_user('permitted', 'permitted@example.com', 'password')
        user.user_permissions.set([
            Permission.objects.get(codename='add_basicmodel'),
            Permission.objects.get(codename='change_basicmodel'),
            Permission.objects.get(codename='delete_basicmodel')
        ])

        user = User.objects.create_user('updateonly', 'updateonly@example.com', 'password')
        user.user_permissions.set([
            Permission.objects.get(codename='change_basicmodel'),
        ])

        self.permitted_credentials = basic_auth_header('permitted', 'password')
        self.disallowed_credentials = basic_auth_header('disallowed', 'password')
        self.updateonly_credentials = basic_auth_header('updateonly', 'password')

        BasicModel(text='foo').save()

    def test_has_create_permissions(self):
        request = factory.post('/', {'text': 'foobar'}, format='json',
                               HTTP_AUTHORIZATION=self.permitted_credentials)
        response = root_view(request, pk=1)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_api_root_view_discard_default_django_model_permission(self):
        """
        We check that DEFAULT_PERMISSION_CLASSES can
        apply to APIRoot view. More specifically we check expected behavior of
        ``_ignore_model_permissions`` attribute support.
        """
        request = factory.get('/', format='json',
                              HTTP_AUTHORIZATION=self.permitted_credentials)
        request.resolver_match = ResolverMatch('get', (), {})
        response = api_root_view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_queryset_has_create_permissions(self):
        request = factory.post('/', {'text': 'foobar'}, format='json',
                               HTTP_AUTHORIZATION=self.permitted_credentials)
        response = get_queryset_list_view(request, pk=1)
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

    def test_options_permitted(self):
        request = factory.options(
            '/',
            HTTP_AUTHORIZATION=self.permitted_credentials
        )
        response = root_view(request, pk='1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('actions', response.data)
        self.assertEqual(list(response.data['actions']), ['POST'])

        request = factory.options(
            '/1',
            HTTP_AUTHORIZATION=self.permitted_credentials
        )
        response = instance_view(request, pk='1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('actions', response.data)
        self.assertEqual(list(response.data['actions']), ['PUT'])

    def test_options_disallowed(self):
        request = factory.options(
            '/',
            HTTP_AUTHORIZATION=self.disallowed_credentials
        )
        response = root_view(request, pk='1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('actions', response.data)

        request = factory.options(
            '/1',
            HTTP_AUTHORIZATION=self.disallowed_credentials
        )
        response = instance_view(request, pk='1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('actions', response.data)

    def test_options_updateonly(self):
        request = factory.options(
            '/',
            HTTP_AUTHORIZATION=self.updateonly_credentials
        )
        response = root_view(request, pk='1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('actions', response.data)

        request = factory.options(
            '/1',
            HTTP_AUTHORIZATION=self.updateonly_credentials
        )
        response = instance_view(request, pk='1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('actions', response.data)
        self.assertEqual(list(response.data['actions']), ['PUT'])

    def test_empty_view_does_not_assert(self):
        request = factory.get('/1', HTTP_AUTHORIZATION=self.permitted_credentials)
        response = empty_list_view(request, pk=1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_calling_method_not_allowed(self):
        request = factory.generic('METHOD_NOT_ALLOWED', '/', HTTP_AUTHORIZATION=self.permitted_credentials)
        response = root_view(request)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        request = factory.generic('METHOD_NOT_ALLOWED', '/1', HTTP_AUTHORIZATION=self.permitted_credentials)
        response = instance_view(request, pk='1')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_check_auth_before_queryset_call(self):
        class View(RootView):
            def get_queryset(_):
                self.fail('should not reach due to auth check')
        view = View.as_view()

        request = factory.get('/', HTTP_AUTHORIZATION='')
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_queryset_assertions(self):
        class View(views.APIView):
            authentication_classes = [authentication.BasicAuthentication]
            permission_classes = [permissions.DjangoModelPermissions]
        view = View.as_view()

        request = factory.get('/', HTTP_AUTHORIZATION=self.permitted_credentials)
        msg = 'Cannot apply DjangoModelPermissions on a view that does not set `.queryset` or have a `.get_queryset()` method.'
        with self.assertRaisesMessage(AssertionError, msg):
            view(request)

        # Faulty `get_queryset()` methods should trigger the above "view does not have a queryset" assertion.
        class View(RootView):
            def get_queryset(self):
                return None
        view = View.as_view()

        request = factory.get('/', HTTP_AUTHORIZATION=self.permitted_credentials)
        with self.assertRaisesMessage(AssertionError, 'View.get_queryset() returned None'):
            view(request)


class BasicPermModel(models.Model):
    text = models.CharField(max_length=100)

    class Meta:
        app_label = 'tests'


class BasicPermSerializer(serializers.ModelSerializer):
    class Meta:
        model = BasicPermModel
        fields = '__all__'


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
    queryset = BasicPermModel.objects.all()
    serializer_class = BasicPermSerializer
    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [ViewObjectPermissions]


object_permissions_view = ObjectPermissionInstanceView.as_view()


class ObjectPermissionListView(generics.ListAPIView):
    queryset = BasicPermModel.objects.all()
    serializer_class = BasicPermSerializer
    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [ViewObjectPermissions]


object_permissions_list_view = ObjectPermissionListView.as_view()


class GetQuerysetObjectPermissionInstanceView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BasicPermSerializer
    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [ViewObjectPermissions]

    def get_queryset(self):
        return BasicPermModel.objects.all()


get_queryset_object_permissions_view = GetQuerysetObjectPermissionInstanceView.as_view()


@unittest.skipUnless('guardian' in settings.INSTALLED_APPS, 'django-guardian not installed')
class ObjectPermissionsIntegrationTests(TestCase):
    """
    Integration tests for the object level permissions API.
    """
    def setUp(self):
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
        model_name = BasicPermModel._meta.model_name
        app_label = BasicPermModel._meta.app_label
        f = '{}_{}'.format
        perms = {
            'view': f('view', model_name),
            'change': f('change', model_name),
            'delete': f('delete', model_name)
        }
        for perm in perms.values():
            perm = '{}.{}'.format(app_label, perm)
            assign_perm(perm, everyone)
        everyone.user_set.add(*users.values())

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
        request = factory.patch(
            '/1', {'text': 'foobar'}, format='json',
            HTTP_AUTHORIZATION=self.credentials['writeonly']
        )
        response = object_permissions_view(request, pk='1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('text'), 'foobar')

    def test_cannot_update_permissions(self):
        request = factory.patch(
            '/1', {'text': 'foobar'}, format='json',
            HTTP_AUTHORIZATION=self.credentials['deleteonly']
        )
        response = object_permissions_view(request, pk='1')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_update_permissions_non_existing(self):
        request = factory.patch(
            '/999', {'text': 'foobar'}, format='json',
            HTTP_AUTHORIZATION=self.credentials['deleteonly']
        )
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

    def test_can_read_get_queryset_permissions(self):
        """
        same as ``test_can_read_permissions`` but with a view
        that rely on ``.get_queryset()`` instead of ``.queryset``.
        """
        request = factory.get('/1', HTTP_AUTHORIZATION=self.credentials['readonly'])
        response = get_queryset_object_permissions_view(request, pk='1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # Read list
    # Note: this previously tested `DjangoObjectPermissionsFilter`, which has
    # since been moved to a separate package. These now act as sanity checks.
    def test_can_read_list_permissions(self):
        request = factory.get('/', HTTP_AUTHORIZATION=self.credentials['readonly'])
        response = object_permissions_list_view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0].get('id'), 1)

    def test_cannot_method_not_allowed(self):
        request = factory.generic('METHOD_NOT_ALLOWED', '/', HTTP_AUTHORIZATION=self.credentials['readonly'])
        response = object_permissions_list_view(request)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class BasicPerm(permissions.BasePermission):
    def has_permission(self, request, view):
        return False


class BasicPermWithDetail(permissions.BasePermission):
    message = 'Custom: You cannot access this resource'
    code = 'permission_denied_custom'

    def has_permission(self, request, view):
        return False


class BasicObjectPerm(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return False


class BasicObjectPermWithDetail(permissions.BasePermission):
    message = 'Custom: You cannot access this resource'
    code = 'permission_denied_custom'

    def has_object_permission(self, request, view, obj):
        return False


class PermissionInstanceView(generics.RetrieveUpdateDestroyAPIView):
    queryset = BasicModel.objects.all()
    serializer_class = BasicSerializer


class DeniedView(PermissionInstanceView):
    permission_classes = (BasicPerm,)


class DeniedViewWithDetail(PermissionInstanceView):
    permission_classes = (BasicPermWithDetail,)


class DeniedObjectView(PermissionInstanceView):
    permission_classes = (BasicObjectPerm,)


class DeniedObjectViewWithDetail(PermissionInstanceView):
    permission_classes = (BasicObjectPermWithDetail,)


denied_view = DeniedView.as_view()

denied_view_with_detail = DeniedViewWithDetail.as_view()

denied_object_view = DeniedObjectView.as_view()

denied_object_view_with_detail = DeniedObjectViewWithDetail.as_view()


class CustomPermissionsTests(TestCase):
    def setUp(self):
        BasicModel(text='foo').save()
        User.objects.create_user('username', 'username@example.com', 'password')
        credentials = basic_auth_header('username', 'password')
        self.request = factory.get('/1', format='json', HTTP_AUTHORIZATION=credentials)
        self.custom_message = 'Custom: You cannot access this resource'
        self.custom_code = 'permission_denied_custom'

    def test_permission_denied(self):
        response = denied_view(self.request, pk=1)
        detail = response.data.get('detail')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertNotEqual(detail, self.custom_message)
        self.assertNotEqual(detail.code, self.custom_code)

    def test_permission_denied_with_custom_detail(self):
        response = denied_view_with_detail(self.request, pk=1)
        detail = response.data.get('detail')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(detail, self.custom_message)
        self.assertEqual(detail.code, self.custom_code)

    def test_permission_denied_for_object(self):
        response = denied_object_view(self.request, pk=1)
        detail = response.data.get('detail')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertNotEqual(detail, self.custom_message)
        self.assertNotEqual(detail.code, self.custom_code)

    def test_permission_denied_for_object_with_custom_detail(self):
        response = denied_object_view_with_detail(self.request, pk=1)
        detail = response.data.get('detail')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(detail, self.custom_message)
        self.assertEqual(detail.code, self.custom_code)


class PermissionsCompositionTests(TestCase):

    def setUp(self):
        self.username = 'john'
        self.email = 'lennon@thebeatles.com'
        self.password = 'password'
        self.user = User.objects.create_user(
            self.username,
            self.email,
            self.password
        )
        self.client.login(username=self.username, password=self.password)

    def test_and_false(self):
        request = factory.get('/1', format='json')
        request.user = AnonymousUser()
        composed_perm = permissions.IsAuthenticated & permissions.AllowAny
        assert composed_perm().has_permission(request, None) is False

    def test_and_true(self):
        request = factory.get('/1', format='json')
        request.user = self.user
        composed_perm = permissions.IsAuthenticated & permissions.AllowAny
        assert composed_perm().has_permission(request, None) is True

    def test_or_false(self):
        request = factory.get('/1', format='json')
        request.user = AnonymousUser()
        composed_perm = permissions.IsAuthenticated | permissions.AllowAny
        assert composed_perm().has_permission(request, None) is True

    def test_or_true(self):
        request = factory.get('/1', format='json')
        request.user = self.user
        composed_perm = permissions.IsAuthenticated | permissions.AllowAny
        assert composed_perm().has_permission(request, None) is True

    def test_not_false(self):
        request = factory.get('/1', format='json')
        request.user = AnonymousUser()
        composed_perm = ~permissions.IsAuthenticated
        assert composed_perm().has_permission(request, None) is True

    def test_not_true(self):
        request = factory.get('/1', format='json')
        request.user = self.user
        composed_perm = ~permissions.AllowAny
        assert composed_perm().has_permission(request, None) is False

    def test_several_levels_without_negation(self):
        request = factory.get('/1', format='json')
        request.user = self.user
        composed_perm = (
            permissions.IsAuthenticated &
            permissions.IsAuthenticated &
            permissions.IsAuthenticated &
            permissions.IsAuthenticated
        )
        assert composed_perm().has_permission(request, None) is True

    def test_several_levels_and_precedence_with_negation(self):
        request = factory.get('/1', format='json')
        request.user = self.user
        composed_perm = (
            permissions.IsAuthenticated &
            ~ permissions.IsAdminUser &
            permissions.IsAuthenticated &
            ~(permissions.IsAdminUser & permissions.IsAdminUser)
        )
        assert composed_perm().has_permission(request, None) is True

    def test_several_levels_and_precedence(self):
        request = factory.get('/1', format='json')
        request.user = self.user
        composed_perm = (
            permissions.IsAuthenticated &
            permissions.IsAuthenticated |
            permissions.IsAuthenticated &
            permissions.IsAuthenticated
        )
        assert composed_perm().has_permission(request, None) is True

    def test_or_lazyness(self):
        request = factory.get('/1', format='json')
        request.user = AnonymousUser()

        with mock.patch.object(permissions.AllowAny, 'has_permission', return_value=True) as mock_allow:
            with mock.patch.object(permissions.IsAuthenticated, 'has_permission', return_value=False) as mock_deny:
                composed_perm = (permissions.AllowAny | permissions.IsAuthenticated)
                hasperm = composed_perm().has_permission(request, None)
                assert hasperm is True
                assert mock_allow.call_count == 1
                mock_deny.assert_not_called()

        with mock.patch.object(permissions.AllowAny, 'has_permission', return_value=True) as mock_allow:
            with mock.patch.object(permissions.IsAuthenticated, 'has_permission', return_value=False) as mock_deny:
                composed_perm = (permissions.IsAuthenticated | permissions.AllowAny)
                hasperm = composed_perm().has_permission(request, None)
                assert hasperm is True
                assert mock_deny.call_count == 1
                assert mock_allow.call_count == 1

    def test_object_or_lazyness(self):
        request = factory.get('/1', format='json')
        request.user = AnonymousUser()

        with mock.patch.object(permissions.AllowAny, 'has_object_permission', return_value=True) as mock_allow:
            with mock.patch.object(permissions.IsAuthenticated, 'has_object_permission', return_value=False) as mock_deny:
                composed_perm = (permissions.AllowAny | permissions.IsAuthenticated)
                hasperm = composed_perm().has_object_permission(request, None, None)
                assert hasperm is True
                assert mock_allow.call_count == 1
                mock_deny.assert_not_called()

        with mock.patch.object(permissions.AllowAny, 'has_object_permission', return_value=True) as mock_allow:
            with mock.patch.object(permissions.IsAuthenticated, 'has_object_permission', return_value=False) as mock_deny:
                composed_perm = (permissions.IsAuthenticated | permissions.AllowAny)
                hasperm = composed_perm().has_object_permission(request, None, None)
                assert hasperm is True
                assert mock_deny.call_count == 1
                assert mock_allow.call_count == 1

    def test_and_lazyness(self):
        request = factory.get('/1', format='json')
        request.user = AnonymousUser()

        with mock.patch.object(permissions.AllowAny, 'has_permission', return_value=True) as mock_allow:
            with mock.patch.object(permissions.IsAuthenticated, 'has_permission', return_value=False) as mock_deny:
                composed_perm = (permissions.AllowAny & permissions.IsAuthenticated)
                hasperm = composed_perm().has_permission(request, None)
                assert hasperm is False
                assert mock_allow.call_count == 1
                assert mock_deny.call_count == 1

        with mock.patch.object(permissions.AllowAny, 'has_permission', return_value=True) as mock_allow:
            with mock.patch.object(permissions.IsAuthenticated, 'has_permission', return_value=False) as mock_deny:
                composed_perm = (permissions.IsAuthenticated & permissions.AllowAny)
                hasperm = composed_perm().has_permission(request, None)
                assert hasperm is False
                assert mock_deny.call_count == 1
                mock_allow.assert_not_called()

    def test_object_and_lazyness(self):
        request = factory.get('/1', format='json')
        request.user = AnonymousUser()

        with mock.patch.object(permissions.AllowAny, 'has_object_permission', return_value=True) as mock_allow:
            with mock.patch.object(permissions.IsAuthenticated, 'has_object_permission', return_value=False) as mock_deny:
                composed_perm = (permissions.AllowAny & permissions.IsAuthenticated)
                hasperm = composed_perm().has_object_permission(request, None, None)
                assert hasperm is False
                assert mock_allow.call_count == 1
                assert mock_deny.call_count == 1

        with mock.patch.object(permissions.AllowAny, 'has_object_permission', return_value=True) as mock_allow:
            with mock.patch.object(permissions.IsAuthenticated, 'has_object_permission', return_value=False) as mock_deny:
                composed_perm = (permissions.IsAuthenticated & permissions.AllowAny)
                hasperm = composed_perm().has_object_permission(request, None, None)
                assert hasperm is False
                assert mock_deny.call_count == 1
                mock_allow.assert_not_called()
