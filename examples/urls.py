from django.conf.urls.defaults import patterns, include
#from django.contrib import admin
from djangorestframework.resource import Resource

#admin.autodiscover()

class RootResource(Resource):
    """This is the sandbox for the examples provided with django-rest-framework.

    These examples are here to help you get a better idea of the some of the
    features of django-rest-framework API, such as automatic form and model validation,
    support for multiple input and output media types, etc...

    Please feel free to browse, create, edit and delete the resources here, either
    in the browser, from the command line, or programmatically."""
    allowed_methods = anon_allowed_methods = ('GET',)

    def get(self, request, auth):
        return {'Simple Resource example': self.reverse('resourceexample.views.ExampleResource'),
                'Simple ModelResource example': self.reverse('modelresourceexample.views.MyModelRootResource'),
                'Object store API (Resource)': self.reverse('objectstore.views.ObjectStoreRoot'),
                'A pygments pastebin API (Resource + forms)': self.reverse('pygments_api.views.PygmentsRoot'),
                'Blog posts API (ModelResource)': self.reverse('blogpost.views.BlogPostRoot'),}


urlpatterns = patterns('',
    (r'^$', RootResource),
    (r'^model-resource-example/', include('modelresourceexample.urls')),
    (r'^resource-example/', include('resourceexample.urls')),
    (r'^object-store/', include('objectstore.urls')),
    (r'^pygments/', include('pygments_api.urls')),
    (r'^blog-post/', include('blogpost.urls')),
    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
    (r'^accounts/logout/$', 'django.contrib.auth.views.logout'),
    #(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    #(r'^admin/', include(admin.site.urls)),
)
