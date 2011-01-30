from django.conf.urls.defaults import patterns

urlpatterns = patterns('pygments_api.views',
    (r'^$', 'PygmentsRoot'), 
    (r'^([a-zA-Z0-9-]+)/$', 'PygmentsInstance'),
)
