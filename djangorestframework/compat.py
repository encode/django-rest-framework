"""Compatability module to provide support for backwards compatability with older versions of django/python"""

# django.test.client.RequestFactory (Django >= 1.3) 
try:
    from django.test.client import RequestFactory

except ImportError:
    from django.test import Client
    from django.core.handlers.wsgi import WSGIRequest
    
    # From: http://djangosnippets.org/snippets/963/
    # Lovely stuff
    class RequestFactory(Client):
        """
        Class that lets you create mock Request objects for use in testing.
        
        Usage:
        
        rf = RequestFactory()
        get_request = rf.get('/hello/')
        post_request = rf.post('/submit/', {'foo': 'bar'})
        
        This class re-uses the django.test.client.Client interface, docs here:
        http://www.djangoproject.com/documentation/testing/#the-test-client
        
        Once you have a request object you can pass it to any view function, 
        just as if that view had been hooked up using a URLconf.
        
        """
        def request(self, **request):
            """
            Similar to parent class, but returns the request object as soon as it
            has created it.
            """
            environ = {
                'HTTP_COOKIE': self.cookies,
                'PATH_INFO': '/',
                'QUERY_STRING': '',
                'REQUEST_METHOD': 'GET',
                'SCRIPT_NAME': '',
                'SERVER_NAME': 'testserver',
                'SERVER_PORT': 80,
                'SERVER_PROTOCOL': 'HTTP/1.1',
            }
            environ.update(self.defaults)
            environ.update(request)
            return WSGIRequest(environ)

# django.views.generic.View (Django >= 1.3)
try:
    from django.views.generic import View
except:
    from django import http
    from django.utils.functional import update_wrapper
    # from django.utils.log import getLogger
    # from django.utils.decorators import classonlymethod
    
    # logger = getLogger('django.request') - We'll just drop support for logger if running Django <= 1.2
    # Might be nice to fix this up sometime to allow djangorestframework.compat.View to match 1.3's View more closely
    
    class View(object):
        """
        Intentionally simple parent class for all views. Only implements
        dispatch-by-method and simple sanity checking.
        """
    
        http_method_names = ['get', 'post', 'put', 'delete', 'head', 'options', 'trace']
    
        def __init__(self, **kwargs):
            """
            Constructor. Called in the URLconf; can contain helpful extra
            keyword arguments, and other things.
            """
            # Go through keyword arguments, and either save their values to our
            # instance, or raise an error.
            for key, value in kwargs.iteritems():
                setattr(self, key, value)
    
        # @classonlymethod - We'll just us classmethod instead if running Django <= 1.2
        @classmethod
        def as_view(cls, **initkwargs):
            """
            Main entry point for a request-response process.
            """
            # sanitize keyword arguments
            for key in initkwargs:
                if key in cls.http_method_names:
                    raise TypeError(u"You tried to pass in the %s method name as a "
                                    u"keyword argument to %s(). Don't do that."
                                    % (key, cls.__name__))
                if not hasattr(cls, key):
                    raise TypeError(u"%s() received an invalid keyword %r" % (
                        cls.__name__, key))
    
            def view(request, *args, **kwargs):
                self = cls(**initkwargs)
                return self.dispatch(request, *args, **kwargs)
    
            # take name and docstring from class
            update_wrapper(view, cls, updated=())
    
            # and possible attributes set by decorators
            # like csrf_exempt from dispatch
            update_wrapper(view, cls.dispatch, assigned=())
            return view
    
        def dispatch(self, request, *args, **kwargs):
            # Try to dispatch to the right method; if a method doesn't exist,
            # defer to the error handler. Also defer to the error handler if the
            # request method isn't on the approved list.
            if request.method.lower() in self.http_method_names:
                handler = getattr(self, request.method.lower(), self.http_method_not_allowed)
            else:
                handler = self.http_method_not_allowed
            self.request = request
            self.args = args
            self.kwargs = kwargs
            return handler(request, *args, **kwargs)
    
        def http_method_not_allowed(self, request, *args, **kwargs):
            allowed_methods = [m for m in self.http_method_names if hasattr(self, m)]
            #logger.warning('Method Not Allowed (%s): %s' % (request.method, request.path),
            #    extra={
            #        'status_code': 405,
            #        'request': self.request
            #    }
            #)
            return http.HttpResponseNotAllowed(allowed_methods)