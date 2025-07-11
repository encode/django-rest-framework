from collections.abc import Iterable

from django.conf import settings
from django.contrib.auth.decorators import login_required, REDIRECT_FIELD_NAME
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from guardian.utils import get_user_obj_perms_model
UserObjectPermission = get_user_obj_perms_model()
from guardian.utils import get_40x_or_None, get_anonymous_user
from guardian.shortcuts import get_objects_for_user


class LoginRequiredMixin:
    """
    A login required mixin for use with class based views. This Class is a
    light wrapper around the `login_required` decorator and hence function
    parameters are just attributes defined on the class.

    Due to parent class order traversal this mixin must be added as the left
    most mixin of a view.

    The mixin has exactly the same flow as `login_required` decorator:

        If the user isn't logged in, redirect to ``settings.LOGIN_URL``, passing
        the current absolute path in the query string. Example:
        ``/accounts/login/?next=/polls/3/``.

        If the user is logged in, execute the view normally. The view code is
        free to assume the user is logged in.

    **Class Settings**

    ``LoginRequiredMixin.redirect_field_name``

        *Default*: ``'next'``

    ``LoginRequiredMixin.login_url``

        *Default*: ``settings.LOGIN_URL``

    """
    redirect_field_name = REDIRECT_FIELD_NAME
    login_url = settings.LOGIN_URL

    def dispatch(self, request, *args, **kwargs):
        return login_required(redirect_field_name=self.redirect_field_name,
                              login_url=self.login_url)(
            super().dispatch
        )(request, *args, **kwargs)


class PermissionRequiredMixin:
    """
    A view mixin that verifies if the current logged in user has the specified
    permission by wrapping the ``request.user.has_perm(..)`` method.

    If a `get_object()` method is defined either manually or by including
    another mixin (for example ``SingleObjectMixin``) or ``self.object`` is
    defined then the permission will be tested against that specific instance,
    alternatively you can specify `get_permission_object()` method if ``self.object``
    or `get_object()` does not return the object against you want to test permission

    .. note:
       Testing of a permission against a specific object instance requires an
       authentication backend that supports. Please see ``django-guardian`` to
       add object level permissions to your project.

    The mixin does the following:

        If the user isn't logged in, redirect to settings.LOGIN_URL, passing
        the current absolute path in the query string. Example:
        /accounts/login/?next=/polls/3/.

        If the `raise_exception` is set to True than rather than redirect to
        login page a `PermissionDenied` (403) is raised.

        If the user is logged in, and passes the permission check than the view
        is executed normally.

    **Example Usage**::

        class SecureView(PermissionRequiredMixin, View):
            ...
            permission_required = 'auth.change_user'
            ...

    **Class Settings**

    ``PermissionRequiredMixin.permission_required``

        *Default*: ``None``, must be set to either a string or list of strings
        in format: *<app_label>.<permission_codename>*.

    ``PermissionRequiredMixin.login_url``

        *Default*: ``settings.LOGIN_URL``

    ``PermissionRequiredMixin.redirect_field_name``

        *Default*: ``'next'``

    ``PermissionRequiredMixin.return_403``

        *Default*: ``False``. Returns 403 error page instead of redirecting
        user.

    ``PermissionRequiredMixin.return_404``

        *Default*: ``False``. Returns 404 error page instead of redirecting
        user.

    ``PermissionRequiredMixin.raise_exception``

        *Default*: ``False``

        `permission_required` - the permission to check of form "<app_label>.<permission codename>"
                                i.e. 'polls.can_vote' for a permission on a model in the polls application.

    ``PermissionRequiredMixin.accept_global_perms``

        *Default*: ``False``,  If accept_global_perms would be set to True, then
         mixing would first check for global perms, if none found, then it will
         proceed to check object level permissions.

    ``PermissionRequiredMixin.permission_object``
         *Default*: ``(not set)``, object against which test the permission; if not set fallback
         to ``self.get_permission_object()`` which return ``self.get_object()``
         or ``self.object`` by default.

    ``PermissionRequiredMixin.any_perm``

        *Default*: ``False``. if True, any of permission in sequence is accepted.

    """
    # default class view settings
    login_url = settings.LOGIN_URL
    permission_required = None
    redirect_field_name = REDIRECT_FIELD_NAME
    return_403 = False
    return_404 = False
    raise_exception = False
    accept_global_perms = False
    any_perm = False

    def get_required_permissions(self, request=None):
        """
        Returns list of permissions in format *<app_label>.<codename>* that
        should be checked against *request.user* and *object*. By default, it
        returns list from ``permission_required`` attribute.

        :param request: Original request.
        """
        if isinstance(self.permission_required, str):
            perms = [self.permission_required]
        elif isinstance(self.permission_required, Iterable):
            perms = [p for p in self.permission_required]
        else:
            raise ImproperlyConfigured("'PermissionRequiredMixin' requires "
                                       "'permission_required' attribute to be set to "
                                       "'<app_label>.<permission codename>' but is set to '%s' instead"
                                       % self.permission_required)
        return perms

    def get_permission_object(self):
        if hasattr(self, 'permission_object'):
            return self.permission_object
        return (hasattr(self, 'get_object') and self.get_object() or
                getattr(self, 'object', None))

    def check_permissions(self, request):
        """
        Checks if *request.user* has all permissions returned by
        *get_required_permissions* method.

        :param request: Original request.
        """
        obj = self.get_permission_object()

        forbidden = get_40x_or_None(request,
                                    perms=self.get_required_permissions(
                                        request),
                                    obj=obj,
                                    login_url=self.login_url,
                                    redirect_field_name=self.redirect_field_name,
                                    return_403=self.return_403,
                                    return_404=self.return_404,
                                    accept_global_perms=self.accept_global_perms,
                                    any_perm=self.any_perm,
                                    )
        if forbidden:
            self.on_permission_check_fail(request, forbidden, obj=obj)
        if forbidden and self.raise_exception:
            raise PermissionDenied()
        return forbidden

    def on_permission_check_fail(self, request, response, obj=None):
        """
        Method called upon permission check fail. By default it does nothing and
        should be overridden, if needed.

        :param request: Original request
        :param response: 403 response returned by *check_permissions* method.
        :param obj: Object that was fetched from the view (using ``get_object``
          method or ``object`` attribute, in that order).
        """

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        self.args = args
        self.kwargs = kwargs
        response = self.check_permissions(request)
        if response:
            return response
        return super().dispatch(request, *args, **kwargs)


class GuardianUserMixin:

    @staticmethod
    def get_anonymous():
        return get_anonymous_user()

    def add_obj_perm(self, perm, obj):
        return UserObjectPermission.objects.assign_perm(perm, self, obj)

    def del_obj_perm(self, perm, obj):
        return UserObjectPermission.objects.remove_perm(perm, self, obj)


class PermissionListMixin:
    """
    A view mixin that filter object in queryset for the current logged by required permission.

    **Example Usage**::

        class SecureView(PermissionListMixin, ListView):
            ...
            permission_required = 'articles.view_article'
            ...

    or::

        class SecureView(PermissionListMixin, ListView):
            ...
            permission_required = 'auth.change_user'
            get_objects_for_user_extra_kwargs = {'use_groups': False}
            ...

    **Class Settings**

    ``PermissionListMixin.permission_required``

        *Default*: ``None``, must be set to either a string or list of strings
        in format: *<app_label>.<permission_codename>*.

    ``PermissionListMixin.get_objects_for_user_extra_kwargs``

        *Default*: ``{}``,  A extra params to pass for ```guardian.shortcuts.get_objects_for_user```

    """
    permission_required = None
    get_objects_for_user_extra_kwargs = {}

    def get_required_permissions(self, request=None):
        """
        Returns list of permissions in format *<app_label>.<codename>* that
        should be checked against *request.user* and *object*. By default, it
        returns list from ``permission_required`` attribute.

        :param request: Original request.
        """
        if isinstance(self.permission_required, str):
            perms = [self.permission_required]
        elif isinstance(self.permission_required, Iterable):
            perms = [p for p in self.permission_required]
        else:
            raise ImproperlyConfigured("'PermissionRequiredMixin' requires "
                                       "'permission_required' attribute to be set to "
                                       "'<app_label>.<permission codename>' but is set to '%s' instead"
                                       % self.permission_required)
        return perms

    def get_get_objects_for_user_kwargs(self, queryset):
        """
        Returns dict of kwargs that should be pass to ```get_objects_for_user```.

        :param request: Queryset to filter
        """
        return dict(user=self.request.user,
                    perms=self.get_required_permissions(self.request),
                    klass=queryset,
                    **self.get_objects_for_user_extra_kwargs)

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        return get_objects_for_user(**self.get_get_objects_for_user_kwargs(qs))
