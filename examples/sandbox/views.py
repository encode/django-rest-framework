"""The root view for the examples provided with Django REST framework"""

from django.core.urlresolvers import reverse
from djangorestframework.views import View


class Sandbox(View):
    """This is the sandbox for the examples provided with [Django REST framework](http://django-rest-framework.org).

    These examples are provided to help you get a better idea of some of the features of RESTful APIs created using the framework.

    All the example APIs allow anonymous access, and can be navigated either through the browser or from the command line...

        bash: curl -X GET http://api.django-rest-framework.org/                           # (Use default renderer)
        bash: curl -X GET http://api.django-rest-framework.org/ -H 'Accept: text/plain'   # (Use plaintext documentation renderer)

    The examples provided:

    1. A basic example using the [Resource](http://django-rest-framework.org/library/resource.html) class.
    2. A basic example using the [ModelResource](http://django-rest-framework.org/library/modelresource.html) class.
    3. An basic example using Django 1.3's [class based views](http://docs.djangoproject.com/en/dev/topics/class-based-views/) and djangorestframework's [RendererMixin](http://django-rest-framework.org/library/renderers.html).
    4. A generic object store API.
    5. A code highlighting API.
    6. A blog posts and comments API.
    7. A basic example using permissions.

    Please feel free to browse, create, edit and delete the resources in these examples."""

    def get(self, request):
        return [{'name': 'Simple Resource example', 'url': reverse('example-resource')},
                {'name': 'Simple ModelResource example', 'url': reverse('model-resource-root')},
                {'name': 'Simple Mixin-only example', 'url': reverse('mixin-view')},
                {'name': 'Object store API', 'url': reverse('object-store-root')},
                {'name': 'Code highlighting API', 'url': reverse('pygments-root')},
                {'name': 'Blog posts API', 'url': reverse('blog-posts-root')},
                {'name': 'Permissions example', 'url': reverse('permissions-example')}
                ]
