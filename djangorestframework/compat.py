"""
The :mod:`compatability` module provides support for backwards compatability with older versions of django/python.
"""

# cStringIO only if it's available
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO


# parse_qs 
try:
    # python >= ?
    from urlparse import parse_qs
except ImportError:
    # python <= ?
    from cgi import parse_qs

   
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
        Class that lets you create mock :obj:`Request` objects for use in testing.
        
        Usage::
        
            rf = RequestFactory()
            get_request = rf.get('/hello/')
            post_request = rf.post('/submit/', {'foo': 'bar'})
        
        This class re-uses the :class:`django.test.client.Client` interface. Of which
        you can find the docs here__.
        
        __ http://www.djangoproject.com/documentation/testing/#the-test-client
        
        Once you have a `request` object you can pass it to any :func:`view` function, 
        just as if that :func:`view` had been hooked up using a URLconf.
        """
        def request(self, **request):
            """
            Similar to parent class, but returns the :obj:`request` object as soon as it
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
except ImportError:
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


try:
    import markdown
    import re
    
    class CustomSetextHeaderProcessor(markdown.blockprocessors.BlockProcessor):
        """
        Override `markdown`'s :class:`SetextHeaderProcessor`, so that ==== headers are <h2> and ---- headers are <h3>.
        
        We use <h1> for the resource name.
        """
    
        # Detect Setext-style header. Must be first 2 lines of block.
        RE = re.compile(r'^.*?\n[=-]{3,}', re.MULTILINE)
    
        def test(self, parent, block):
            return bool(self.RE.match(block))
    
        def run(self, parent, blocks):
            lines = blocks.pop(0).split('\n')
            # Determine level. ``=`` is 1 and ``-`` is 2.
            if lines[1].startswith('='):
                level = 2
            else:
                level = 3
            h = markdown.etree.SubElement(parent, 'h%d' % level)
            h.text = lines[0].strip()
            if len(lines) > 2:
                # Block contains additional lines. Add to  master blocks for later.
                blocks.insert(0, '\n'.join(lines[2:]))
            
    def apply_markdown(text):
        """
        Simple wrapper around :func:`markdown.markdown` to apply our :class:`CustomSetextHeaderProcessor`,
        and also set the base level of '#' style headers to <h2>.
        """
        
        extensions = ['headerid(level=2)']
        safe_mode = False,
        output_format = markdown.DEFAULT_OUTPUT_FORMAT

        md = markdown.Markdown(extensions=markdown.load_extensions(extensions),
                               safe_mode=safe_mode, 
                               output_format=output_format)
        md.parser.blockprocessors['setextheader'] = CustomSetextHeaderProcessor(md.parser)
        return md.convert(text)

except ImportError:
    apply_markdown = None