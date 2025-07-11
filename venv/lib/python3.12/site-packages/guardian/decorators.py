from django.apps import apps
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.db.models import Model
from django.db.models.base import ModelBase
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404
from django.utils.functional import wraps
from guardian.exceptions import GuardianError
from guardian.utils import get_40x_or_None


def permission_required(perm, lookup_variables=None, **kwargs):
    """
    Decorator for views that checks whether a user has a particular permission
    enabled.

    Optionally, instances for which check should be made may be passed as an
    second argument or as a tuple parameters same as those passed to
    ``get_object_or_404`` but must be provided as pairs of strings. This way
    decorator can fetch i.e. ``User`` instance based on performed request and
    check permissions on it (without this, one would need to fetch user instance
    at view's logic and check permission inside a view).

    :param login_url: if denied, user would be redirected to location set by
      this parameter. Defaults to ``django.conf.settings.LOGIN_URL``.
    :param redirect_field_name: name of the parameter passed if redirected.
      Defaults to ``django.contrib.auth.REDIRECT_FIELD_NAME``.
    :param return_403: if set to ``True`` then instead of redirecting to the
      login page, response with status code 403 is returned (
      ``django.http.HttpResponseForbidden`` instance or rendered template -
      see :setting:`GUARDIAN_RENDER_403`). Defaults to ``False``.
    :param return_404: if set to ``True`` then instead of redirecting to the
      login page, response with status code 404 is returned (
      ``django.http.HttpResponseNotFound`` instance or rendered template -
      see :setting:`GUARDIAN_RENDER_404`). Defaults to ``False``.
    :param accept_global_perms: if set to ``True``, then *object level
      permission* would be required **only if user does NOT have global
      permission** for target *model*. If turned on, makes this decorator
      like an extension over standard
      ``django.contrib.admin.decorators.permission_required`` as it would
      check for global permissions first. Defaults to ``False``.

    Examples::

        @permission_required('auth.change_user', return_403=True)
        def my_view(request):
            return HttpResponse('Hello')

        @permission_required('auth.change_user', (User, 'username', 'username'))
        def my_view(request, username):
            '''
            auth.change_user permission would be checked based on given
            'username'. If view's parameter would be named ``name``, we would
            rather use following decorator::

                @permission_required('auth.change_user', (User, 'username', 'name'))
            '''
            user = get_object_or_404(User, username=username)
            return user.get_absolute_url()

        @permission_required('auth.change_user',
            (User, 'username', 'username', 'groups__name', 'group_name'))
        def my_view(request, username, group_name):
            '''
            Similar to the above example, here however we also make sure that
            one of user's group is named same as request's ``group_name`` param.
            '''
            user = get_object_or_404(User, username=username,
                group__name=group_name)
            return user.get_absolute_url()

    """
    login_url = kwargs.pop('login_url', settings.LOGIN_URL)
    redirect_field_name = kwargs.pop(
        'redirect_field_name', REDIRECT_FIELD_NAME)
    return_403 = kwargs.pop('return_403', False)
    return_404 = kwargs.pop('return_404', False)
    accept_global_perms = kwargs.pop('accept_global_perms', False)

    # Check if perm is given as string in order not to decorate
    # view function itself which makes debugging harder
    if not isinstance(perm, str):
        raise GuardianError("First argument must be in format: "
                            "'app_label.codename or a callable which return similar string'")

    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            # if more than one parameter is passed to the decorator we try to
            # fetch object for which check would be made
            obj = None
            if lookup_variables:
                model, lookups = lookup_variables[0], lookup_variables[1:]
                # Parse model
                if isinstance(model, str):
                    splitted = model.split('.')
                    if len(splitted) != 2:
                        raise GuardianError("If model should be looked up from "
                                            "string it needs format: 'app_label.ModelClass'")
                    model = apps.get_model(*splitted)
                elif issubclass(model.__class__, (Model, ModelBase, QuerySet)):
                    pass
                else:
                    raise GuardianError("First lookup argument must always be "
                                        "a model, string pointing at app/model or queryset. "
                                        "Given: %s (type: %s)" % (model, type(model)))
                # Parse lookups
                if len(lookups) % 2 != 0:
                    raise GuardianError("Lookup variables must be provided "
                                        "as pairs of lookup_string and view_arg")
                lookup_dict = {}
                for lookup, view_arg in zip(lookups[::2], lookups[1::2]):
                    if view_arg not in kwargs:
                        raise GuardianError("Argument %s was not passed "
                                            "into view function" % view_arg)
                    lookup_dict[lookup] = kwargs[view_arg]
                obj = get_object_or_404(model, **lookup_dict)

            response = get_40x_or_None(request, perms=[perm], obj=obj,
                                       login_url=login_url, redirect_field_name=redirect_field_name,
                                       return_403=return_403, return_404=return_404, accept_global_perms=accept_global_perms)
            if response:
                return response
            return view_func(request, *args, **kwargs)
        return wraps(view_func)(_wrapped_view)
    return decorator


def permission_required_or_403(perm, *args, **kwargs):
    """
    Simple wrapper for permission_required decorator.

    Standard Django's permission_required decorator redirects user to login page
    in case permission check failed. This decorator may be used to return
    HttpResponseForbidden (status 403) instead of redirection.

    The only difference between ``permission_required`` decorator is that this
    one always set ``return_403`` parameter to ``True``.
    """
    kwargs['return_403'] = True
    return permission_required(perm, *args, **kwargs)


def permission_required_or_404(perm, *args, **kwargs):
    """
    Simple wrapper for permission_required decorator.

    Standard Django's permission_required decorator redirects user to login page
    in case permission check failed. This decorator may be used to return
    HttpResponseNotFound (status 404) instead of redirection.

    The only difference between ``permission_required`` decorator is that this
    one always set ``return_404`` parameter to ``True``.
    """
    kwargs['return_404'] = True
    return permission_required(perm, *args, **kwargs)
