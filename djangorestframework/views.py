"""
The :mod:`views` module provides the Views you will most probably
be subclassing in your implementation.

By setting or modifying class attributes on your view, you change it's predefined behaviour.
"""

from django.core.urlresolvers import set_script_prefix
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from djangorestframework.compat import View as DjangoView
from djangorestframework.response import Response, ErrorResponse
from djangorestframework.mixins import *
from djangorestframework import resources, renderers, parsers, authentication, permissions, status


__all__ = (
    'View',
    'ModelView',
    'InstanceModelView',
    'ListModelView',
    'ListOrCreateModelView'
)



class View(ResourceMixin, RequestMixin, ResponseMixin, AuthMixin, DjangoView):
    """
    Handles incoming requests and maps them to REST operations.
    Performs request deserialization, response serialization, authentication and input validation.
    """

    """
    The resource to use when validating requests and filtering responses,
    or `None` to use default behaviour.
    """
    resource = None

    """
    List of renderers the resource can serialize the response with, ordered by preference.
    """
    renderers = ( renderers.JSONRenderer,
                  renderers.DocumentingHTMLRenderer,
                  renderers.DocumentingXHTMLRenderer,
                  renderers.DocumentingPlainTextRenderer,
                  renderers.XMLRenderer )
    
    """
    List of parsers the resource can parse the request with.
    """
    parsers = ( parsers.JSONParser,
                parsers.FormParser,
                parsers.MultiPartParser )

    """
    List of all authenticating methods to attempt.
    """
    authentication = ( authentication.UserLoggedInAuthentication,
                       authentication.BasicAuthentication )
    
    """
    List of all permissions that must be checked.
    """
    permissions = ( permissions.FullAnonAccess, )
    
    
    @classmethod
    def as_view(cls, **initkwargs):
        """
        Override the default :meth:`as_view` to store an instance of the view
        as an attribute on the callable function.  This allows us to discover
        information about the view when we do URL reverse lookups. 
        """
        view = super(View, cls).as_view(**initkwargs)
        view.cls_instance = cls(**initkwargs)
        return view


    @property
    def allowed_methods(self):
        """
        Return the list of allowed HTTP methods, uppercased.
        """
        return [method.upper() for method in self.http_method_names if hasattr(self, method)]


    def http_method_not_allowed(self, request, *args, **kwargs):
        """
        Return an HTTP 405 error if an operation is called which does not have a handler method.        
        """
        raise ErrorResponse(status.HTTP_405_METHOD_NOT_ALLOWED,
                            {'detail': 'Method \'%s\' not allowed on this resource.' % self.method})


    def initial(self, request, *args, **kargs):
        """
        Hook for any code that needs to run prior to anything else.
        Required if you want to do things like set `request.upload_handlers` before
        the authentication and dispatch handling is run.
        """
        pass


    def add_header(self, field, value):
        """
        Add *field* and *value* to the :attr:`headers` attribute of the :class:`View` class. 
        """
        self.headers[field] = value


    # Note: session based authentication is explicitly CSRF validated,
    # all other authentication is CSRF exempt.
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        self.request = request
        self.args = args
        self.kwargs = kwargs
        self.headers = {}

        # Calls to 'reverse' will not be fully qualified unless we set the scheme/host/port here.
        prefix = '%s://%s' % (request.is_secure() and 'https' or 'http', request.get_host())
        set_script_prefix(prefix)

        try:
            self.initial(request, *args, **kwargs)
        
            # Authenticate and check request has the relevant permissions
            self._check_permissions()

            # Get the appropriate handler method
            if self.method.lower() in self.http_method_names:
                handler = getattr(self, self.method.lower(), self.http_method_not_allowed)
            else:
                handler = self.http_method_not_allowed

            response_obj = handler(request, *args, **kwargs)

            # Allow return value to be either HttpResponse, Response, or an object, or None
            if isinstance(response_obj, HttpResponse):
                return response_obj
            elif isinstance(response_obj, Response):
                response = response_obj
            elif response_obj is not None:
                response = Response(status.HTTP_200_OK, response_obj)
            else:
                response = Response(status.HTTP_204_NO_CONTENT)

            # Pre-serialize filtering (eg filter complex objects into natively serializable types)
            response.cleaned_content = self.filter_response(response.raw_content)
    
        except ErrorResponse, exc:
            response = exc.response
        
        # Always add these headers.
        #
        # TODO - this isn't actually the correct way to set the vary header,
        # also it's currently sub-obtimal for HTTP caching - need to sort that out. 
        response.headers['Allow'] = ', '.join(self.allowed_methods)
        response.headers['Vary'] = 'Authenticate, Accept'
        
        # merge with headers possibly set at some point in the view
        response.headers.update(self.headers)
        
        return self.render(response)    


class ModelView(View):
    """A RESTful view that maps to a model in the database."""
    resource = resources.ModelResource

class InstanceModelView(InstanceMixin, ReadModelMixin, UpdateModelMixin, DeleteModelMixin, ModelView):
    """A view which provides default operations for read/update/delete against a model instance."""
    _suffix = 'Instance'

class ListModelView(ListModelMixin, ModelView):
    """A view which provides default operations for list, against a model in the database."""   
    _suffix = 'List'

class ListOrCreateModelView(ListModelMixin, CreateModelMixin, ModelView):
    """A view which provides default operations for list and create, against a model in the database."""   
    _suffix = 'List'
