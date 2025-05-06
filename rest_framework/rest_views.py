from django import VERSION as DJANGO_VERSION
from django.db import models
from django.urls import path
from django.utils.decorators import classonlymethod
from django.views.decorators.csrf import csrf_exempt

from rest_framework.views import APIView


class RESTViewMethod:

    def __init__(
        self,
        http_method: str,
        path: str,
        url_name: str,
        view_method
    ):
        self.http_method = http_method
        self.path = path
        self.url_name = url_name
        self.view_method = view_method


def get(path: str, url_name: str):
    def decorator(view_method):
        return RESTViewMethod(
            http_method='get',
            path=path,
            url_name=url_name,
            view_method=view_method,
        )

    return decorator


def post(path: str, url_name: str):
    def decorator(view_method):
        return RESTViewMethod(
            http_method='post',
            path=path,
            url_name=url_name,
            view_method=view_method,
        )

    return decorator


def put(path: str, url_name: str):
    def decorator(view_method):
        return RESTViewMethod(
            http_method='put',
            path=path,
            url_name=url_name,
            view_method=view_method,
        )

    return decorator


def patch(path: str, url_name: str):
    def decorator(view_method):
        return RESTViewMethod(
            http_method='patch',
            path=path,
            url_name=url_name,
            view_method=view_method,
        )

    return decorator


def delete(path: str, url_name: str):
    def decorator(view_method):
        return RESTViewMethod(
            http_method='delete',
            path=path,
            url_name=url_name,
            view_method=view_method,
        )

    return decorator


class RESTViewMetaclass(type):

    def __new__(cls, name, bases, attrs):
        _all_actions: dict[str, list[tuple[str, str, str]]] = {}
        http_method_path_pairs = set()
        url_names_by_path = {}

        for key, value in attrs.items():
            if isinstance(value, RESTViewMethod):
                if (value.http_method, value.path) in http_method_path_pairs:
                    raise ValueError(f"{cls.__name__} has multiple methods with the same HTTP method and path")

                http_method_path_pairs.add((value.http_method, value.path))

                url_names_by_path.setdefault(value.path, set()).add(value.url_name)
                if len(url_names_by_path[value.path]) > 1:
                    raise ValueError(
                        f"{cls.__name__} has multiple methods with the same path {value.path}, but different URL names"
                    )

                http_method_path_pairs.add((value.http_method, value.path))
                _all_actions.setdefault(value.path, [])
                _all_actions[value.path].append((value.http_method, value.view_method.__name__, value.url_name))
                attrs[key] = value.view_method

        attrs['_all_actions'] = _all_actions
        return type.__new__(cls, name, bases, attrs)


class RESTView(APIView, metaclass=RESTViewMetaclass):
    """
    A View that allows handling any HTTP methods and URL paths. Use special decorators to specify URl path
    and URl name for handlers. These decorators moved to a class attribute at runtime.

    Example:
        class UserAPI(RESTView):

            @get(path='v1/users/', url_name='users')
            def list(self, request):
                ...

            @get(path='v1/users/<int:user_id>/', url_name='user_detail')
            def retrieve(self, request, user_id: int):
                ...

            @post(path='v1/users/', url_name='users')
            def create(self, request):
                ...

            @patch(path='v1/users/<int:user_id>/change_password/', url_name='user_change_password')
            def change_password(self, request, user_id: int):
                ...

    To use this View, you have to comply with these rules:
    1. Use special decorators for all handlers
    2. All identical URL paths must have identical URL names
    3. Special decorators have to be the last in order
    4. All custom decorators have to be wrapped with functools.wraps or manually copy the docstrings
    """

    @classonlymethod
    def unwrap_url_patterns(cls, **initkwargs):
        """
        Create classes for all URL paths for Django urlpatterns interface

        Example:
            urlpatterns = [
                *UserAPI.unwrap_url_patterns(),
            ]
        """
        urlpatterns = []
        for url_path, attrs in cls._all_actions.items():
            view = cls.as_view(url_path=url_path, **initkwargs)
            urlpatterns.append(path(url_path, view, name=attrs[0][2]))

        return urlpatterns

    @classmethod
    def as_view(cls, url_path: str, **initkwargs):
        """
        Store the generated class on the view function for URL path. Don't use this method.
        """
        if isinstance(getattr(cls, 'queryset', None), models.query.QuerySet):
            def force_evaluation():
                raise RuntimeError(
                    'Do not evaluate the `.queryset` attribute directly, '
                    'as the result will be cached and reused between requests. '
                    'Use `.all()` or call `.get_queryset()` instead.'
                )
            cls.queryset._fetch_all = force_evaluation

        fork_cls = type(cls.__name__, cls.__bases__, dict(cls.__dict__))
        actions = {}
        for http_method, view_method_name, url_name in cls._all_actions[url_path]:
            actions[http_method] = view_method_name

        if 'get' in actions and 'head' not in actions:
            actions['head'] = actions['get']

        if 'options' not in actions:
            # use ApiView.options
            actions['options'] = 'options'

        fork_cls.actions = actions
        view = super(APIView, fork_cls).as_view(**initkwargs)
        view.cls = fork_cls
        view.initkwargs = initkwargs

        # Exempt all DRF views from Django's LoginRequiredMiddleware. Users should set
        # DEFAULT_PERMISSION_CLASSES to 'rest_framework.permissions.IsAuthenticated' instead
        if DJANGO_VERSION >= (5, 1):
            view.login_required = False

        # Note: session based authentication is explicitly CSRF validated,
        # all other authentication is CSRF exempt.
        return csrf_exempt(view)

    def dispatch(self, request, *args, **kwargs):
        """
        `.dispatch()` is pretty much the same as ApiView dispatch
        """
        self.args = args
        self.kwargs = kwargs
        request = self.initialize_request(request, *args, **kwargs)
        self.request = request
        self.headers = self.default_response_headers  # deprecate?

        try:
            self.initial(request, *args, **kwargs)

            view_method_name = self.actions.get(request.method.lower())
            handler = (
                getattr(self, view_method_name, self.http_method_not_allowed)
                if view_method_name
                else self.http_method_not_allowed
            )
            response = handler(request, *args, **kwargs)

        except Exception as exc:
            response = self.handle_exception(exc)

        self.response = self.finalize_response(request, response, *args, **kwargs)
        return self.response


__all__ = ['get', 'post', 'put', 'patch', 'delete', 'RESTView']
