from django.conf.urls.defaults import patterns

urlpatterns = patterns('objectstore.views',
    (r'^$', 'ObjectStoreRoot'), 
    (r'^(?P<key>[A-Za-z0-9_-]{1,64})/$', 'StoredObject'),
)
