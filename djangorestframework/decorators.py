from functools import wraps
from django.utils.decorators import available_attrs
from djangorestframework.views import APIView


class LazyViewCreator(object):

    """
    This class is responsible for dynamically creating an APIView subclass that
    will wrap a function-based view. Instances of this class are created
    by the function-based view decorators (below), and each decorator is
    responsible for setting attributes on the instance that will eventually be
    copied onto the final class-based view. The CBV gets created lazily the first
    time it's needed, and then cached for future use.

    This is done so that the ordering of stacked decorators is irrelevant.
    """

    def __init__(self):

        # Each item in this dictionary will be copied onto the final
        # class-based view that gets created when this object is called
        self.final_view_attrs = {
            'renderer_classes': APIView.renderer_classes,
            'parser_classes': APIView.parser_classes,
            'authentication_classes': APIView.authentication_classes,
            'throttle_classes': APIView.throttle_classes,
            'permission_classes': APIView.permission_classes,
        }
        self._cached_view = None

    @property
    def view(self):
        """
        Accessor for the dynamically created class-based view. This will
        be created if necessary and cached for next time.
        """

        if self._cached_view is None:

            class WrappedAPIView(APIView):
                pass

            for attr, value in self.final_view_attrs.items():
                setattr(WrappedAPIView, attr, value)

            self._cached_view = WrappedAPIView.as_view()

        return self._cached_view

    def __call__(self, *args, **kwargs):
        """
        This is the actual code that gets run per-request
        """
        return self.view(*args, **kwargs)

    @staticmethod
    def maybe_create(func):
        """
        If the argument is already an instance of LazyViewCreator,
        just return it. Otherwise, create a new one.
        """
        if isinstance(func, LazyViewCreator):
            return func
        return LazyViewCreator()


def api_view(allowed_methods):
    """
    Decorator for function based views.

        @api_view(['GET', 'POST'])
        def my_view(request):
            # request will be an instance of `Request`
            # `Response` objects will have .request set automatically
            # APIException instances will be handled
    """

    def decorator(func):
        wrapper = LazyViewCreator.maybe_create(func)

        @wraps(func, assigned=available_attrs(func))
        def handler(self, *args, **kwargs):
            return func(*args, **kwargs)

        for method in allowed_methods:
            wrapper.final_view_attrs[method.lower()] = handler

        return wrapper
    return decorator


def _create_attribute_setting_decorator(attribute):
    def decorator(value):
        def inner(func):
            wrapper = LazyViewCreator.maybe_create(func)
            wrapper.final_view_attrs[attribute] = value
            return wrapper
        return inner
    return decorator


renderer_classes = _create_attribute_setting_decorator('renderer_classes')
parser_classes = _create_attribute_setting_decorator('parser_classes')
authentication_classes = _create_attribute_setting_decorator('authentication_classes')
throttle_classes = _create_attribute_setting_decorator('throttle_classes')
permission_classes = _create_attribute_setting_decorator('permission_classes')
