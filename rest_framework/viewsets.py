from functools import update_wrapper
from django.utils.decorators import classonlymethod
from rest_framework import views, generics, mixins


class ViewSetMixin(object):
    """
    This is the magic.

    Overrides `.as_view()` so that it takes an `actions` keyword that performs
    the binding of HTTP methods to actions on the Resource.

    For example, to create a concrete view binding the 'GET' and 'POST' methods
    to the 'list' and 'create' actions...

    view = MyViewSet.as_view({'get': 'list', 'post': 'create'})
    """
    _is_viewset = True

    @classonlymethod
    def as_view(cls, actions=None, name_suffix=None, **initkwargs):
        """
        Main entry point for a request-response process.

        Because of the way class based views create a closure around the
        instantiated view, we need to totally reimplement `.as_view`,
        and slightly modify the view function that is created and returned.
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
            # This is the bit that's different to a standard view
            for method, action in actions.items():
                handler = getattr(self, action)
                setattr(self, method, handler)

            # Patch this in as it's otherwise only present from 1.5 onwards
            if hasattr(self, 'get') and not hasattr(self, 'head'):
                self.head = self.get

            # And continue as usual
            return self.dispatch(request, *args, **kwargs)

        # take name and docstring from class
        update_wrapper(view, cls, updated=())

        # and possible attributes set by decorators
        # like csrf_exempt from dispatch
        update_wrapper(view, cls.dispatch, assigned=())

        view.cls = cls
        return view


class ViewSet(ViewSetMixin, views.APIView):
    pass


# Note the inheritence of both MultipleObjectAPIView *and* SingleObjectAPIView
# is a bit weird given the diamond inheritence, but it will work for now.
# There's some implementation clean up that can happen later.
class ModelViewSet(mixins.CreateModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin,
                    mixins.ListModelMixin,
                    ViewSetMixin,
                    generics.GenericAPIView):
    pass


class ReadOnlyModelViewSet(mixins.RetrieveModelMixin,
                           mixins.ListModelMixin,
                           ViewSetMixin,
                           generics.GenericAPIView):
    pass
