from django.test.testcases import TestCase
from djangorestframework.generics import RootAPIView, InstanceAPIView, ListAPIView, DetailAPIView
from djangorestframework.resources import ModelResource
from djangorestframework.routers import DefaultResourceRouter
from djangorestframework.serializers import Serializer, ModelSerializer
from djangorestframework.tests.models import Company, Employee
from django.conf.urls.defaults import patterns, url, include
from django.core.urlresolvers import reverse, NoReverseMatch
import random
import string

__all__ = ('DefaultResourceRouterTestCase',)

class DummyUrlConfModule(object):

    def __init__(self, object_with_urls):
        self._object_with_urls = object_with_urls

    @property
    def urlpatterns(self):
        urlpatterns = patterns('',
            url(r'^', include(self._object_with_urls.urls, namespace='api')),
        )
        return urlpatterns


class DefaultResourceRouterTestCase(TestCase):

    def setUp(self):
        self.api = DefaultResourceRouter()
        self.urlconfmodule = DummyUrlConfModule(self.api)

    def test_list_view(self):
        # Check that the URL gets registered
        self.api.register(Company)
        list_url = reverse('api:company_collection', urlconf=self.urlconfmodule)
        self.assertEqual(list_url, '/companys/')

    def test_instance_view(self):
        self.api.register(Company)
        company = Company(name='Acme Ltd')
        company.save()

        # Check that the URL gets registered
        instance_url = reverse(
            'api:company_instance', urlconf=self.urlconfmodule,
            kwargs={'pk':company.id},
        )
        self.assertEqual(instance_url, '/companys/' + str(company.id) + '/')

    def test_instance_view_with_nonumeric_primary_key(self):
        """
        Check that the api can properly reverse urls for models with
        non-numeric primary keys
        """
        self.api.register(Employee)
        employee = Employee(employee_id='EMP001')
        employee.save()

        instance_url = reverse(
            'api:employee_instance', urlconf=self.urlconfmodule,
            kwargs={'pk':employee.employee_id}
        )
        self.assertEqual(instance_url, '/employees/EMP001/')

    def test_with_different_name(self):
        class CompanyResource (ModelResource):
            id_field_name = 'name'

        self.api.register(Company, CompanyResource)
        company = Company(name='Acme')
        company.save()

        instance_url = reverse(
            'api:company_instance', urlconf=self.urlconfmodule,
            kwargs={'name':company.name},
        )
        self.assertEqual(instance_url, '/companys/Acme/')

    def test_with_different_collection_name(self):
        class CompanyResource (ModelResource):
            collection_name = 'companies'

        self.api.register(Company, CompanyResource)

        list_url = reverse('api:company_collection', urlconf=self.urlconfmodule)
        self.assertEqual(list_url, '/companies/')

        instance_url = reverse('api:company_instance', urlconf=self.urlconfmodule, kwargs={'pk':1})
        self.assertEqual(instance_url, '/companies/1/')

    def test_with_default_collection_view_class(self):
        self.api.register(Company)
        company = Company(name='Acme Ltd')
        company.save()

        view = self.api.urls[0]._callback
        self.assertIsInstance(view.cls_instance, RootAPIView)
        self.assertIsInstance(view.cls_instance, ModelResource)

    def test_with_default_instance_view_class(self):
        self.api.register(Company)

        view = self.api.urls[1]._callback
        self.assertIsInstance(view.cls_instance, InstanceAPIView)
        self.assertIsInstance(view.cls_instance, ModelResource)

    def test_with_different_collection_view_class(self):
        class CompanyResource(ModelResource):
            collection_view_class = ListAPIView
        self.api.register(Company, CompanyResource)

        view = self.api.urls[0]._callback
        self.assertIsInstance(view.cls_instance, ListAPIView)
        self.assertIsInstance(view.cls_instance, ModelResource)

    def test_with_different_instance_view_class(self):
        class CompanyResource(ModelResource):
            instance_view_class = DetailAPIView
        self.api.register(Company, CompanyResource)

        view = self.api.urls[1]._callback
        self.assertIsInstance(view.cls_instance, DetailAPIView)
        self.assertIsInstance(view.cls_instance, ModelResource)

    def test_with_default_serializer_class(self):
        self.api.register(Company)

        view = self.api.urls[0]._callback
        self.assertIs(view.cls_instance.serializer_class, ModelSerializer)

    def test_with_different_serializer_class(self):
        class CompanySerializer(Serializer):
            pass
        class CompanyResource(ModelResource):
            serializer_class = CompanySerializer
        self.api.register(Company, CompanyResource)

        view = self.api.urls[0]._callback
        self.assertIs(view.cls_instance.serializer_class, CompanySerializer)
