##### RESOURCES AND ROUTERS ARE NOT YET IMPLEMENTED - PLACEHOLDER ONLY #####

from functools import update_wrapper
import inspect
from django.utils.decorators import classonlymethod
from rest_framework import views, generics


def wrapped(source, dest):
    """
    Copy public, non-method attributes from source to dest, and return dest.
    """
    for attr in [attr for attr in dir(source)
                 if not attr.startswith('_') and not inspect.ismethod(attr)]:
        setattr(dest, attr, getattr(source, attr))
    return dest


##### RESOURCES AND ROUTERS ARE NOT YET IMPLEMENTED - PLACEHOLDER ONLY #####

class ResourceMixin(object):
    """
    Clone Django's `View.as_view()` behaviour *except* using REST framework's
    'method -> action' binding for resources.
    """

    @classonlymethod
    def as_view(cls, actions, **initkwargs):
        """
        Main entry point for a request-response process.
        """
        # sanitize keyword arguments
        for key in initkwargs:
            if key in cls.http_method_names:
                raise TypeError("You tried to pass in the %s method name as a "
                                "keyword argument to %s(). Don't do that."
                                % (key, cls.__name__))
            if not hasattr(cls, key):
                raise TypeError("%s() received an invalid keyword %r" % (
                    cls.__name__, key))

        def view(request, *args, **kwargs):
            self = cls(**initkwargs)

            # Bind methods to actions
            for method, action in actions.items():
                handler = getattr(self, action)
                setattr(self, method, handler)

            # As you were, solider.
            if hasattr(self, 'get') and not hasattr(self, 'head'):
                self.head = self.get
            return self.dispatch(request, *args, **kwargs)

        # take name and docstring from class
        update_wrapper(view, cls, updated=())

        # and possible attributes set by decorators
        # like csrf_exempt from dispatch
        update_wrapper(view, cls.dispatch, assigned=())
        return view


##### RESOURCES AND ROUTERS ARE NOT YET IMPLEMENTED - PLACEHOLDER ONLY #####

class Resource(ResourceMixin, views.APIView):
    pass


##### RESOURCES AND ROUTERS ARE NOT YET IMPLEMENTED - PLACEHOLDER ONLY #####

class ModelResource(ResourceMixin, views.APIView):
    root_class = generics.ListCreateAPIView
    detail_class = generics.RetrieveUpdateDestroyAPIView

    def root_view(self):
        return wrapped(self, self.root_class())

    def detail_view(self):
        return wrapped(self, self.detail_class())

    def list(self, request, *args, **kwargs):
        return self.root_view().list(request, args, kwargs)

    def create(self, request, *args, **kwargs):
        return self.root_view().create(request, args, kwargs)

    def retrieve(self, request, *args, **kwargs):
        return self.detail_view().retrieve(request, args, kwargs)

    def update(self, request, *args, **kwargs):
        return self.detail_view().update(request, args, kwargs)

    def destroy(self, request, *args, **kwargs):
        return self.detail_view().destroy(request, args, kwargs)
