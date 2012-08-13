from django.conf.urls.defaults import patterns, url
from djangorestframework.views import ListOrCreateModelView, InstanceModelView
from modelresourceexample.resources import MyModelResource

my_model_list = ListOrCreateModelView.as_view(resource=MyModelResource)
my_model_instance = InstanceModelView.as_view(resource=MyModelResource)

urlpatterns = patterns('',
    url(r'^$', my_model_list, name='model-resource-root'),
    url(r'^(?P<id>[0-9]+)/$', my_model_instance, name='model-resource-instance'),
)
