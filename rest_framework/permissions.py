"""
Provides a set of pluggable permission policies.
"""
from __future__ import unicode_literals
import inspect
import warnings

SAFE_METHODS = ['GET', 'HEAD', 'OPTIONS']

from rest_framework.compat import oauth2_provider_scope


class BasePermission(object):
    """
    A base class from which all permission classes should inherit.
    """

    def has_permission(self, request, view):
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        return True

    def has_object_permission(self, request, view, obj):
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        if len(inspect.getargspec(self.has_permission)[0]) == 4:
            warnings.warn('The `obj` argument in `has_permission` is due to be deprecated. '
                      'Use `has_object_permission()` instead for object permissions.',
                       PendingDeprecationWarning, stacklevel=2)
            return self.has_permission(request, view, obj)
        return True


class AllowAny(BasePermission):
    """
    Allow any access.
    This isn't strictly required, since you could use an empty
    permission_classes list, but it's useful because it makes the intention
    more explicit.
    """
    def has_permission(self, request, view):
        return True


class IsAuthenticated(BasePermission):
    """
    Allows access only to authenticated users.
    """

    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated():
            return True
        return False


class IsAdminUser(BasePermission):
    """
    Allows access only to admin users.
    """

    def has_permission(self, request, view):
        if request.user and request.user.is_staff:
            return True
        return False


class IsAuthenticatedOrReadOnly(BasePermission):
    """
    The request is authenticated as a user, or is a read-only request.
    """

    def has_permission(self, request, view):
        if (request.method in SAFE_METHODS or
            request.user and
            request.user.is_authenticated()):
            return True
        return False


class DjangoModelPermissions(BasePermission):
    """
    The request is authenticated using `django.contrib.auth` permissions.
    See: https://docs.djangoproject.com/en/dev/topics/auth/#permissions

    It ensures that the user is authenticated, and has the appropriate
    `add`/`change`/`delete` permissions on the model.

    This permission will only be applied against view classes that
    provide a `.model` attribute, such as the generic class-based views.
    """

    # Map methods into required permission codes.
    # Override this if you need to also provide 'view' permissions,
    # or if you want to provide custom permission codes.
    perms_map = {
        'GET': [],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }

    def get_required_permissions(self, method, model_cls):
        """
        Given a model and an HTTP method, return the list of permission
        codes that the user is required to have.
        """
        kwargs = {
            'app_label': model_cls._meta.app_label,
            'model_name': model_cls._meta.module_name
        }
        return [perm % kwargs for perm in self.perms_map[method]]

    def has_permission(self, request, view):
        model_cls = getattr(view, 'model', None)
        if not model_cls:
            return True

        perms = self.get_required_permissions(request.method, model_cls)

        if (request.user and
            request.user.is_authenticated() and
            request.user.has_perms(perms)):
            return True
        return False


class TokenHasReadWriteScope(BasePermission):
    """
    The request is authenticated as a user and the token used has the right scope
    """

    def has_permission(self, request, view):
        if not request.auth:
            return False

        read_only = request.method in SAFE_METHODS
        if hasattr(request.auth, 'resource'):  # oauth 1
            if read_only:
                return True
            elif request.auth.resource.is_readonly is False:
                return True
            return False
        elif hasattr(request.auth, 'scope'):   # oauth 2
            scope_valid = lambda scope_wanted_key, scope_had: oauth2_provider_scope.check(
                oauth2_provider_scope.SCOPE_NAME_DICT[scope_wanted_key], scope_had)

            if read_only and scope_valid('read', request.auth.scope):
                return True
            elif scope_valid('write', request.auth.scope):
                return True
            return False
        else:
            # Improperly configured!
            pass
