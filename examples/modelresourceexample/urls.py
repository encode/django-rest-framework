from django.conf.urls.defaults import patterns, url
from modelresourceexample.views import MyModelRootResource, MyModelResource

urlpatterns = patterns('modelresourceexample.views',
    url(r'^$',          MyModelRootResource.as_view(), name='my-model-root-resource'),
    url(r'^([0-9]+)/$', MyModelResource.as_view(), name='my-model-resource'),
)
