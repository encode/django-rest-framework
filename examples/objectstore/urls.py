from django.conf.urls.defaults import patterns, url
from objectstore.views import ObjectStoreRoot, StoredObject

urlpatterns = patterns('objectstore.views',
    url(r'^$', ObjectStoreRoot.as_view(), name='object-store-root'),
    url(r'^(?P<key>[A-Za-z0-9_-]{1,64})/$', StoredObject.as_view(), name='stored-object'),
)
