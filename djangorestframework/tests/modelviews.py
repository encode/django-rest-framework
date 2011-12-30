from django.conf.urls.defaults import patterns, url
from django.test import TestCase
from django.forms import ModelForm
from django.contrib.auth.models import Group, User
from djangorestframework.resources import ModelResource
from djangorestframework.views import ListOrCreateModelView, InstanceModelView
from djangorestframework.tests.models import CustomUser
from djangorestframework.tests.testcases import TestModelsTestCase

class GroupResource(ModelResource):
    model = Group

class UserForm(ModelForm):
    class Meta:
        model = User
        exclude = ('last_login', 'date_joined')

class UserResource(ModelResource):
    model = User
    form = UserForm

class CustomUserResource(ModelResource):
    model = CustomUser

urlpatterns = patterns('',
    url(r'^users/$', ListOrCreateModelView.as_view(resource=UserResource), name='users'),
    url(r'^users/(?P<id>[0-9]+)/$', InstanceModelView.as_view(resource=UserResource)),
    url(r'^customusers/$', ListOrCreateModelView.as_view(resource=CustomUserResource), name='customusers'),
    url(r'^customusers/(?P<id>[0-9]+)/$', InstanceModelView.as_view(resource=CustomUserResource)),
    url(r'^groups/$', ListOrCreateModelView.as_view(resource=GroupResource), name='groups'),
    url(r'^groups/(?P<id>[0-9]+)/$', InstanceModelView.as_view(resource=GroupResource)),
)


class ModelViewTests(TestModelsTestCase):
    """Test the model views djangorestframework provides"""
    urls = 'djangorestframework.tests.modelviews'

    def test_creation(self):
        """Ensure that a model object can be created"""
        self.assertEqual(0, Group.objects.count())

        response = self.client.post('/groups/', {'name': 'foo'})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(1, Group.objects.count())
        self.assertEqual('foo', Group.objects.all()[0].name)

    def test_creation_with_m2m_relation(self):
        """Ensure that a model object with a m2m relation can be created"""
        group = Group(name='foo')
        group.save()
        self.assertEqual(0, User.objects.count())

        response = self.client.post('/users/', {'username': 'bar', 'password': 'baz', 'groups': [group.id]})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(1, User.objects.count())

        user = User.objects.all()[0]
        self.assertEqual('bar', user.username)
        self.assertEqual('baz', user.password)
        self.assertEqual(1, user.groups.count())

        group = user.groups.all()[0]
        self.assertEqual('foo', group.name)

    def test_creation_with_m2m_relation_through(self):
        """
        Ensure that a model object with a m2m relation can be created where that
        relation uses a through table
        """
        group = Group(name='foo')
        group.save()
        self.assertEqual(0, User.objects.count())

        response = self.client.post('/customusers/', {'username': 'bar', 'groups': [group.id]})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(1, CustomUser.objects.count())

        user = CustomUser.objects.all()[0]
        self.assertEqual('bar', user.username)
        self.assertEqual(1, user.groups.count())

        group = user.groups.all()[0]
        self.assertEqual('foo', group.name)
