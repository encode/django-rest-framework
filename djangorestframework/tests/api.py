from django.test.testcases import TestCase
from djangorestframework.builtins import Api, ApiEntry
from djangorestframework.resources import Resource, ModelResource
from djangorestframework.tests.models import Company, Employee
from django.conf.urls.defaults import patterns, url, include
from djangorestframework.views import ListOrCreateModelView, InstanceModelView,\
    ListModelView
from django.core.urlresolvers import reverse, NoReverseMatch
import random
import string

__all__ = ('ApiTestCase', 'ApiEntryTestCase')

class CompanyResource(ModelResource):
    model = Company
    
    
class EmployeeResource(ModelResource):
    model = Employee
    
    
class DummyUrlConfModule(object):
    
    def __init__(self, object_with_urls):
        self._object_with_urls = object_with_urls
        
    @property
    def urlpatterns(self):
        urlpatterns = patterns('', 
            url(r'^', include(self._object_with_urls.urls)),
        )    
        return urlpatterns
    
    
class CustomApiEntry(ApiEntry):
    
    def __init__(self, *args, **kwargs):
        super(CustomApiEntry, self).__init__(*args, **kwargs)
        self.name = 'custom'
    

class ApiTestCase(TestCase):
    
    def setUp(self):
        self.api = Api()
        self.urlconfmodule = DummyUrlConfModule(self.api)
        
    def test_list_view(self):
        # Check that the URL gets registered
        self.api.register(ListModelView, CompanyResource)
        reverse('api:company', urlconf=self.urlconfmodule)
                
    def test_instance_view(self):
        self.api.register(InstanceModelView, CompanyResource)
        company = Company(name='Acme Ltd')
        company.save()
        # Check that the URL gets registered
        reverse(
            'api:company_change', urlconf=self.urlconfmodule,
            kwargs={'pk':company.id}, 
        )
        
    def test_instance_view_with_nonumeric_primary_key(self):
        """
        Check that the api can properly reverse urls for models with
        non-numeric primary keys 
        """
        self.api.register(InstanceModelView, EmployeeResource)
        employee = Employee(employee_id='EMP001')
        employee.save()
        reverse(
            'api:employee_change', urlconf=self.urlconfmodule,
            kwargs={'pk':employee.employee_id}
        )
        
    def test_with_different_name(self):
        self.api.register(InstanceModelView, CompanyResource, name='abcdef')
        company = Company(name='Acme Ltd')
        company.save()
        # Check that the URL gets registered
        reverse(
            'api:abcdef_change', urlconf=self.urlconfmodule,
            kwargs={'pk':company.id}, 
        )
        
    def test_with_prefix(self):
        self.api.register(
            InstanceModelView, CompanyResource, namespace='abcdef'
        )
        company = Company(name='Acme Ltd')
        company.save()
        # Check that the URL gets registered
        reverse(
            'api:abcdef:company_change', urlconf=self.urlconfmodule,
            kwargs={'pk':company.id}, 
        )
        
    def test_custom_api_entry_class_1(self):
        """
        Ensure that an Api object which has a custom `api_entry_class` passed
        to the constructor
        """
        self.api = Api(api_entry_class=CustomApiEntry)
        self.urlconfmodule = DummyUrlConfModule(self.api)
        
        # Check that the URL gets registered
        self.api.register(ListModelView, CompanyResource)
        reverse('api:custom', urlconf=self.urlconfmodule)
        self.assertRaises(
            NoReverseMatch, reverse, 'api:company', urlconf=self.urlconfmodule
        )
        
    def test_custom_api_entry_class_2(self):
        """
        Ensure that an Api object which has a custom `api_entry_class` assigned
        to it uses it 
        """
        self.api = Api()
        self.api.api_entry_class = CustomApiEntry
        self.urlconfmodule = DummyUrlConfModule(self.api)
        
        # Check that the URL gets registered
        self.api.register(ListModelView, CompanyResource)
        reverse('api:custom', urlconf=self.urlconfmodule)
        self.assertRaises(
            NoReverseMatch, reverse, 'api:company', urlconf=self.urlconfmodule
        )
        
        
class ApiEntryTestCase(TestCase):
    """
    Test the ApiEntry class
    """
        
    def test_with_different_name(self):
        """
        Ensure that the passed in name is used in the returned URL
        """
        name = ''.join(random.choice(string.letters) for i in xrange(10))
        api_entry = ApiEntry(
            resource=CompanyResource, view=ListModelView, name=name
        )
        urls = api_entry.get_urls()
        self.assertEqual(len(urls), 1)
        self.assert_(urls[0].resolve('%s/' % (name)) is not None)
    
    def test_list_model_view(self):
        """
        Ensure that using a ListModelView returns only a url all objects
        """
        api_entry = ApiEntry(
            resource=CompanyResource, view=ListModelView, name='company'
        )
        urls = api_entry.get_urls()
        self.assertEqual(len(urls), 1)
        self.assert_(urls[0].resolve('company/') is not None)
        self.assert_(urls[0].resolve('company/10/') is None)
        self.assert_(urls[0].resolve('company/dasdsad/') is None)
        
    def test_reverse_by_name_list_model_view(self):
        """
        Ensure the created ListModelView URL patterns can be reversed by name
        """
        api_entry = ApiEntry(
            resource=CompanyResource, view=ListModelView, name='company'
        )
        # Setup the dummy urlconf module
        urlconfmodule = DummyUrlConfModule(api_entry)
        
        # Check that the URL gets registered with a name
        reverse('company', urlconf=urlconfmodule)
        
    def test_reverse_by_name_isntance_model_view(self):
        """
        Ensure the created ListModelView URL patterns can be reversed by name
        """
        api_entry = ApiEntry(
            resource=CompanyResource, view=InstanceModelView, name='company'
        )
        # Setup the dummy urlconf module
        urlconfmodule = DummyUrlConfModule(api_entry)
        
        # Check that the URL gets registered with a name
        reverse('company_change', kwargs={'pk': '10'}, urlconf=urlconfmodule)
        reverse('company_change', kwargs={'pk': 'aaaaa'}, urlconf=urlconfmodule)
    
    def test_instance_model_view(self):
        """
        Ensure that using an InstanceModelView returns a url which requires a 
        primary key
        """
        api_entry = ApiEntry(
            resource=CompanyResource, view=InstanceModelView, name='company'
        )
        urls = api_entry.get_urls()
        self.assertEqual(len(urls), 1)
        self.assert_(urls[0].resolve('company/') is None)
        self.assert_(urls[0].resolve('company/10/') is not None)
        self.assert_(urls[0].resolve('company/abcde/') is not None)
        
    def test_namespaced_names(self):
        """
        Ensure that when a namespace gets passed into the ApiEntry, it is
        reflected in the returned URL
        """
        namespace = ''.join(random.choice(string.letters) for i in xrange(10))
        
        # test list model view
        api_entry = ApiEntry(
            resource=CompanyResource, view=ListModelView, name='company',
            namespace=namespace
        )
        urls = api_entry.get_urls()
        self.assertEqual(len(urls), 1)
        self.assert_(urls[0].resolve('%s/company/' % (namespace)) is not None)
        self.assert_(urls[0].resolve('%s/company/10/' % (namespace)) is None)
        self.assert_(
            urls[0].resolve('%s/company/dasdsad/' % (namespace)) is None
        )
        
        # Test instance model view
        api_entry = ApiEntry(
            resource=CompanyResource, view=InstanceModelView, name='company',
            namespace=namespace
        )
        urls = api_entry.get_urls()
        self.assertEqual(len(urls), 1)
        self.assert_(urls[0].resolve('%s/company/' % (namespace)) is None)
        self.assert_(
            urls[0].resolve('%s/company/10/' % (namespace)) is not None
        )
        self.assert_(
            urls[0].resolve('%s/company/abcde/' % (namespace)) is not None
        )
        
    
    