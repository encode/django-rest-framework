from djangorestframework.views import View
from djangorestframework.resources import ModelResource
from djangorestframework.tests.testcases import TestModelsTestCase
from djangorestframework.compat import RequestFactory
from djangorestframework.tests.models import CustomUser
from django.contrib.auth.models import Group, User

class MockView(View):
    """This is a basic mock view"""
    pass

class TestModelCreation(TestModelsTestCase):
    """Tests on CreateModelMixin"""

    def setUp(self):
        super(TestModelsTestCase, self).setUp()
        self.req = RequestFactory()

    def test_create(self):
        self.assertEquals(0, Group.objects.count())

        class GroupResource(ModelResource):
            model = Group

        request = self.req.post('/groups', data={})
        args = []
        kwargs = {'name': 'foo'}

        resource = GroupResource(view=MockView.as_view())
        resource.create(request, *args, **kwargs)

        self.assertEquals(1, Group.objects.count())
        self.assertEquals('foo', resource.instance.name)

    def test_update(self):
        self.assertEquals(0, Group.objects.count())

        class GroupResource(ModelResource):
            model = Group

        group = Group(name='foo')
        group.save()

        request = self.req.post('/groups', data={})
        args = []
        kwargs = {}
        data = {'name': 'bla'}

        resource = GroupResource(instance=group, view=MockView.as_view())
        resource.update(data, request, *args, **kwargs)

        self.assertEquals('bla', resource.instance.name)

    def test_update_with_m2m_relation(self):
        class UserResource(ModelResource):
            model = User

            def url(self, instance):
                return "/users/%i" % instance.id

        group = Group(name='foo')
        group.save()
        user = User(username='bar')
        user.save()

        form_data = {
            'username': 'bar',
            'password': 'baz',
            'groups': [group.id]
        }
        request = self.req.post('/groups', data=form_data)
        args = []
        kwargs = {}
        cleaned_data = dict(form_data, groups=[group])
        
        resource = UserResource(instance=user, view=MockView.as_view())
        resource.update(cleaned_data, request, *args, **kwargs)

        self.assertEquals(1, resource.instance.groups.count())
        self.assertEquals('foo', resource.instance.groups.all()[0].name)

    def test_update_with_m2m_relation_through(self):
        """
        Tests creation where the m2m relation uses a through table
        """
        class UserResource(ModelResource):
            model = CustomUser

            def url(self, instance):
                return "/customusers/%i" % instance.id

        user = User(username='bar')
        user.save()

        form_data = {'groups': []}
        request = self.req.post('/groups', data=form_data)
        args = []
        kwargs = {}
        cleaned_data = dict(form_data, groups=[])

        resource = UserResource(instance=user, view=MockView.as_view())
        resource.update(cleaned_data, request, *args, **kwargs)

        self.assertEquals(0, resource.instance.groups.count())


        group = Group(name='foo1')
        group.save()

        form_data = {'groups': [group.id]}
        request = self.req.post('/groups', data=form_data)
        cleaned_data = dict(form_data, groups=[group])

        resource.update(cleaned_data, request, *args, **kwargs)

        self.assertEquals(1, resource.instance.groups.count())
        self.assertEquals('foo1', resource.instance.groups.all()[0].name)


        group2 = Group(name='foo2')
        group2.save()

        form_data = {'username': 'bar2', 'groups': [group.id, group2.id]}
        request = self.req.post('/groups', data=form_data)
        cleaned_data = dict(form_data, groups=[group, group2])

        resource.update(cleaned_data, request, *args, **kwargs)

        self.assertEquals(2, resource.instance.groups.count())
        self.assertEquals('foo1', resource.instance.groups.all()[0].name)
        self.assertEquals('foo2', resource.instance.groups.all()[1].name)

