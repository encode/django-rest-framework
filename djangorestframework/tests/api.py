from django.test.testcases import TestCase
from djangorestframework.builtins import DjangoRestFrameworkApi
from djangorestframework.resources import Resource, ModelResource
from djangorestframework.tests.models import Company, Employee
from django.conf.urls.defaults import patterns, url, include
from djangorestframework.views import ListOrCreateModelView, InstanceModelView,\
    ListModelView
from django.core.urlresolvers import reverse

__all__ = ('ApiTestCase',)

class CompanyResource(ModelResource):
    model = Company
    
class EmployeeResource(ModelResource):
    model = Employee
    
class UrlConfModule(object):
    
    def __init__(self, api):
        self.api = api
        
    def _get_urlpatterns(self):
        return patterns('', 
            url(r'^', include(self.api.urls)),
        )
        
    urlpatterns = property(_get_urlpatterns)


class ApiTestCase(TestCase):
    
    def setUp(self):
        self.api = DjangoRestFrameworkApi()
        self.urlconfmodule = UrlConfModule(self.api)
        
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