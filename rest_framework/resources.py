##### RESOURCES AND ROUTERS ARE NOT YET IMPLEMENTED - PLACEHOLDER ONLY #####

from functools import update_wrapper
from django.utils.decorators import classonlymethod
from rest_framework import views, generics, mixins


##### RESOURCES AND ROUTERS ARE NOT YET IMPLEMENTED - PLACEHOLDER ONLY #####

class ResourceMixin(object):
    """
    This is the magic.

    Overrides `.as_view()` so that it takes an `actions` keyword that performs
    the binding of HTTP methods to actions on the Resource.

    For example, to create a concrete view binding the 'GET' and 'POST' methods
    to the 'list' and 'create' actions...

    my_resource = MyResource.as_view({'get': 'list', 'post': 'create'})
    """

    @classonlymethod
    def as_view(cls, actions=None, **initkwargs):
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


class Resource(ResourceMixin, views.APIView):
    pass


# Note the inheritence of both MultipleObjectAPIView *and* SingleObjectAPIView
# is a bit weird given the diamond inheritence, but it will work for now.
# There's some implementation clean up that can happen later.
class ModelResource(mixins.CreateModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin,
                    mixins.ListModelMixin,
                    ResourceMixin,
                    generics.MultipleObjectAPIView,
                    generics.SingleObjectAPIView):
    pass
