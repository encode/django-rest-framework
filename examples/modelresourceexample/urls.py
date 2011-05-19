from django.conf.urls.defaults import patterns, url
from djangorestframework.views import ListOrCreateModelView, InstanceModelView
from djangorestframework.resources import ModelResource
from modelresourceexample.models import MyModel

class MyModelResource(ModelResource):
    model = MyModel
    fields = ('foo', 'bar', 'baz', 'url')
    ordering = ('created',)

urlpatterns = patterns('',
    url(r'^$',          ListOrCreateModelView.as_view(resource=MyModelResource), name='model-resource-root'),
    url(r'^([0-9]+)/$', InstanceModelView.as_view(resource=MyModelResource)),
)
