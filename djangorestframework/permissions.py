"""
The :mod:`permissions` module bundles a set of permission classes that are used
for checking if a request passes a certain set of constraints.

Permission behavior is provided by mixing the :class:`mixins.PermissionsMixin` class into a :class:`View` class.
"""

__all__ = (
    'BasePermission',
    'FullAnonAccess',
    'IsAuthenticated',
    'IsAdminUser',
    'IsUserOrIsAnonReadOnly',
    'PerUserThrottling',
    'PerViewThrottling',
)

SAFE_METHODS = ['GET', 'HEAD', 'OPTIONS']


class BasePermission(object):
    """
    A base class from which all permission classes should inherit.
    """
    def __init__(self, view):
        """
        Permission classes are always passed the current view on creation.
        """
        self.view = view

    def check_permission(self, request, obj=None):
        """
        Should simply return, or raise an :exc:`response.ImmediateResponse`.
        """
        raise NotImplementedError(".check_permission() must be overridden.")


class IsAuthenticated(BasePermission):
    """
    Allows access only to authenticated users.
    """

    def check_permission(self, request, obj=None):
        if request.user and request.user.is_authenticated():
            return True
        return False


class IsAdminUser(BasePermission):
    """
    Allows access only to admin users.
    """

    def check_permission(self, request, obj=None):
        if request.user and request.user.is_staff():
            return True
        return False


class IsAuthenticatedOrReadOnly(BasePermission):
    """
    The request is authenticated as a user, or is a read-only request.
    """

    def check_permission(self, request, obj=None):
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

    This permission should only be used on views with a `ModelResource`.
    """

    # Map methods into required permission codes.
    # Override this if you need to also provide 'read' permissions,
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
            'model_name':  model_cls._meta.module_name
        }
        return [perm % kwargs for perm in self.perms_map[method]]

    def check_permission(self, request, obj=None):
        model_cls = self.view.model
        perms = self.get_required_permissions(request.method, model_cls)

        if (request.user and
            request.user.is_authenticated() and
            request.user.has_perms(perms, obj)):
            return True
        return False
