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

    def __init__(self, wrapped_view):

        self.wrapped_view = wrapped_view

        # Each item in this dictionary will be copied onto the final
        # class-based view that gets created when this object is called
        self.final_view_attrs = {
            'http_method_names': APIView.http_method_names,
            'renderer_classes': APIView.renderer_classes,
            'parser_classes': APIView.parser_classes,
            'authentication_classes': APIView.authentication_classes,
            'throttle_classes': APIView.throttle_classes,
            'permission_classes': APIView.permission_classes,
        }
        self._cached_view = None

    def handler(self, *args, **kwargs):
        return self.wrapped_view(*args, **kwargs)

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

            # Attach the wrapped view function for each of the
            # allowed HTTP methods
            for method in WrappedAPIView.http_method_names:
                setattr(WrappedAPIView, method.lower(), self.handler)

            self._cached_view = WrappedAPIView.as_view()

        return self._cached_view

    def __call__(self, *args, **kwargs):
        """
        This is the actual code that gets run per-request
        """
        return self.view(*args, **kwargs)

    @staticmethod
    def maybe_create(func_or_instance):
        """
        If the argument is already an instance of LazyViewCreator,
        just return it. Otherwise, create a new one.
        """
        if isinstance(func_or_instance, LazyViewCreator):
            return func_or_instance
        return LazyViewCreator(func_or_instance)


def _create_attribute_setting_decorator(attribute, filter=lambda item: item):
    def decorator(value):
        def inner(func):
            wrapper = LazyViewCreator.maybe_create(func)
            wrapper.final_view_attrs[attribute] = filter(value)
            return wrapper
        return inner
    return decorator


api_view = _create_attribute_setting_decorator('http_method_names', filter=lambda methods: [method.lower() for method in methods])
renderer_classes = _create_attribute_setting_decorator('renderer_classes')
parser_classes = _create_attribute_setting_decorator('parser_classes')
authentication_classes = _create_attribute_setting_decorator('authentication_classes')
throttle_classes = _create_attribute_setting_decorator('throttle_classes')
permission_classes = _create_attribute_setting_decorator('permission_classes')
