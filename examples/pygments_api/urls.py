from django.conf.urls.defaults import patterns, url
from pygments_api.views import PygmentsRoot, PygmentsInstance

urlpatterns = patterns('',
    url(r'^$', PygmentsRoot.as_view(), name='pygments-root'),
    url(r'^([a-zA-Z0-9-]+)/$', PygmentsInstance.as_view(), name='pygments-instance'),
)
