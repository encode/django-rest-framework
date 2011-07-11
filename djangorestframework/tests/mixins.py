"""Tests for the status module"""
from django.test import TestCase
from djangorestframework import status
from djangorestframework.compat import RequestFactory
from django.contrib.auth.models import Group, User
from djangorestframework.mixins import CreateModelMixin
from djangorestframework.resources import ModelResource
from djangorestframework.tests.models import CustomUser


class TestModelCreation(TestCase): 
    """Tests on CreateModelMixin"""

    def setUp(self):
        self.req = RequestFactory()

    def test_creation(self):
        self.assertEquals(0, Group.objects.count())

        class GroupResource(ModelResource):
            model = Group

        form_data = {'name': 'foo'}
        request = self.req.post('/groups', data=form_data)
        mixin = CreateModelMixin()
        mixin.resource = GroupResource
        mixin.CONTENT = form_data
        
        response = mixin.post(request)
        self.assertEquals(1, Group.objects.count())
        self.assertEquals('foo', response.cleaned_content.name)
        

    def test_creation_with_m2m_relation(self):
        class UserResource(ModelResource):
            model = User
   
            def url(self, instance):
                return "/users/%i" % instance.id

        group = Group(name='foo')
        group.save()

        form_data = {'username': 'bar', 'password': 'baz', 'groups': [group.id]}        
        request = self.req.post('/groups', data=form_data)
        cleaned_data = dict(form_data)
        cleaned_data['groups'] = [group]
        mixin = CreateModelMixin()
        mixin.resource = UserResource
        mixin.CONTENT = cleaned_data

        response = mixin.post(request)
        self.assertEquals(1, User.objects.count())
        self.assertEquals(1, response.cleaned_content.groups.count())
        self.assertEquals('foo', response.cleaned_content.groups.all()[0].name)
        
    def test_creation_with_m2m_relation_through(self):
        """
        Tests creation where the m2m relation uses a through table
        """
        class UserResource(ModelResource):
            model = CustomUser
   
            def url(self, instance):
                return "/customusers/%i" % instance.id
            
        form_data = {'username': 'bar0', 'groups': []}        
        request = self.req.post('/groups', data=form_data)
        cleaned_data = dict(form_data)
        cleaned_data['groups'] = []
        mixin = CreateModelMixin()
        mixin.resource = UserResource
        mixin.CONTENT = cleaned_data

        response = mixin.post(request)
        self.assertEquals(1, CustomUser.objects.count())
        self.assertEquals(0, response.cleaned_content.groups.count())            

        group = Group(name='foo1')
        group.save()

        form_data = {'username': 'bar1', 'groups': [group.id]}        
        request = self.req.post('/groups', data=form_data)
        cleaned_data = dict(form_data)
        cleaned_data['groups'] = [group]
        mixin = CreateModelMixin()
        mixin.resource = UserResource
        mixin.CONTENT = cleaned_data

        response = mixin.post(request)
        self.assertEquals(2, CustomUser.objects.count())
        self.assertEquals(1, response.cleaned_content.groups.count())
        self.assertEquals('foo1', response.cleaned_content.groups.all()[0].name)
        
        
        group2 = Group(name='foo2')
        group2.save()        
        
        form_data = {'username': 'bar2', 'groups': [group.id, group2.id]}        
        request = self.req.post('/groups', data=form_data)
        cleaned_data = dict(form_data)
        cleaned_data['groups'] = [group, group2]
        mixin = CreateModelMixin()
        mixin.resource = UserResource
        mixin.CONTENT = cleaned_data

        response = mixin.post(request)
        self.assertEquals(3, CustomUser.objects.count())
        self.assertEquals(2, response.cleaned_content.groups.count())
        self.assertEquals('foo1', response.cleaned_content.groups.all()[0].name)
        self.assertEquals('foo2', response.cleaned_content.groups.all()[1].name)
        

