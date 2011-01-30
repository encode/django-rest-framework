from django.conf.urls.defaults import patterns, include
#from django.contrib import admin
from djangorestframework.resource import Resource

#admin.autodiscover()

class RootResource(Resource):
    allowed_methods = anon_allowed_methods = ('GET',)

    def get(self, request, auth):
        return {'simple example': self.reverse('simpleexample.views.MyModelRootResource'),
                'pygments example': self.reverse('pygments_api.views.PygmentsRoot'),
                'object store example': self.reverse('objectstore.views.ObjectStoreRoot'),
                'blog post example': self.reverse('blogpost.views.BlogPostRoot'),}


urlpatterns = patterns('',
    (r'^$', RootResource),
    (r'^simple-example/', include('simpleexample.urls')),
    (r'^object-store/', include('objectstore.urls')),
    (r'^pygments/', include('pygments_api.urls')),
    (r'^blog-post/', include('blogpost.urls')),
    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
    (r'^accounts/logout/$', 'django.contrib.auth.views.logout'),
    #(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    #(r'^admin/', include(admin.site.urls)),
)
