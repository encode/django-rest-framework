"""The root view for the examples provided with Django REST framework"""

from djangorestframework.utils import reverse
from djangorestframework.views import View
from djangorestframework.response import Response


class Sandbox(View):
    """
    This is the sandbox for the examples provided with
    [Django REST framework][1].

    These examples are provided to help you get a better idea of some of the
    features of RESTful APIs created using the framework.

    All the example APIs allow anonymous access, and can be navigated either
    through the browser or from the command line.

    For example, to get the default representation using curl:

        bash: curl -X GET http://rest.ep.io/
    
    Or, to get the plaintext documentation represention:

        bash: curl -X GET http://rest.ep.io/ -H 'Accept: text/plain'

    The examples provided:

    1. A basic example using the [Resource][2] class.
    2. A basic example using the [ModelResource][3] class.
    3. An basic example using Django 1.3's [class based views][4] and
       djangorestframework's [RendererMixin][5].
    4. A generic object store API.
    5. A code highlighting API.
    6. A blog posts and comments API.
    7. A basic example using permissions.
    8. A basic example using enhanced request.

    Please feel free to browse, create, edit and delete the resources in
    these examples.

    [1]: http://django-rest-framework.org
    [2]: http://django-rest-framework.org/library/resource.html
    [3]: http://django-rest-framework.org/library/modelresource.html
    [4]: http://docs.djangoproject.com/en/dev/topics/class-based-views/
    [5]: http://django-rest-framework.org/library/renderers.html
    """

    def get(self, request):
        return Response([
            {'name': 'Simple Resource example',
             'url': reverse('example-resource', request)},
            {'name': 'Simple ModelResource example',
             'url': reverse('model-resource-root', request)},
            {'name': 'Simple Mixin-only example',
             'url': reverse('mixin-view', request)},
            {'name': 'Object store API'
             'url': reverse('object-store-root', request)},
            {'name': 'Code highlighting API',
             'url': reverse('pygments-root', request)},
            {'name': 'Blog posts API',
             'url': reverse('blog-posts-root', request)},
            {'name': 'Permissions example',
             'url': reverse('permissions-example', request)},
            {'name': 'Simple request mixin example',
             'url': reverse('request-example', request)}
        ])
