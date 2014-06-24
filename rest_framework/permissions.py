"""
Provides a set of pluggable permission policies.
"""
from __future__ import unicode_literals
from django.http import Http404
from rest_framework.compat import (get_model_name, oauth2_provider_scope,
                                   oauth2_constants)

SAFE_METHODS = ['GET', 'HEAD', 'OPTIONS']


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
        return request.user and request.user.is_authenticated()


class IsAdminUser(BasePermission):
    """
    Allows access only to admin users.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_staff


class IsAuthenticatedOrReadOnly(BasePermission):
    """
    The request is authenticated as a user, or is a read-only request.
    """

    def has_permission(self, request, view):
        return (request.method in SAFE_METHODS or 
            request.user and 
            request.user.is_authenticated())


class DjangoModelPermissions(BasePermission):
    """
    The request is authenticated using `django.contrib.auth` permissions.
    See: https://docs.djangoproject.com/en/dev/topics/auth/#permissions

    It ensures that the user is authenticated, and has the appropriate
    `add`/`change`/`delete` permissions on the model.

    This permission can only be applied against view classes that
    provide a `.model` or `.queryset` attribute.
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

    authenticated_users_only = True

    def get_required_permissions(self, method, model_cls):
        """
        Given a model and an HTTP method, return the list of permission
        codes that the user is required to have.
        """
        kwargs = {
            'app_label': model_cls._meta.app_label,
            'model_name': get_model_name(model_cls)
        }
        return [perm % kwargs for perm in self.perms_map[method]]

    def has_permission(self, request, view):
        model_cls = getattr(view, 'model', None)
        queryset = getattr(view, 'queryset', None)

        if model_cls is None and queryset is not None:
            model_cls = queryset.model

        # Workaround to ensure DjangoModelPermissions are not applied
        # to the root view when using DefaultRouter.
        if model_cls is None and getattr(view, '_ignore_model_permissions', False):
            return True

        assert model_cls, ('Cannot apply DjangoModelPermissions on a view that'
                           ' does not have `.model` or `.queryset` property.')

        perms = self.get_required_permissions(request.method, model_cls)

        return (request.user and
            (request.user.is_authenticated() or not self.authenticated_users_only) and
            request.user.has_perms(perms))


class DjangoModelPermissionsOrAnonReadOnly(DjangoModelPermissions):
    """
    Similar to DjangoModelPermissions, except that anonymous users are
    allowed read-only access.
    """
    authenticated_users_only = False


class DjangoObjectPermissions(DjangoModelPermissions):
    """
    The request is authenticated using Django's object-level permissions.
    It requires an object-permissions-enabled backend, such as Django Guardian.

    It ensures that the user is authenticated, and has the appropriate
    `add`/`change`/`delete` permissions on the object using .has_perms.

    This permission can only be applied against view classes that
    provide a `.model` or `.queryset` attribute.
    """

    perms_map = {
        'GET': [],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }

    def get_required_object_permissions(self, method, model_cls):
        kwargs = {
            'app_label': model_cls._meta.app_label,
            'model_name': get_model_name(model_cls)
        }
        return [perm % kwargs for perm in self.perms_map[method]]

    def has_object_permission(self, request, view, obj):
        model_cls = getattr(view, 'model', None)
        queryset = getattr(view, 'queryset', None)

        if model_cls is None and queryset is not None:
            model_cls = queryset.model

        perms = self.get_required_object_permissions(request.method, model_cls)
        user = request.user

        if not user.has_perms(perms, obj):
            # If the user does not have permissions we need to determine if
            # they have read permissions to see 403, or not, and simply see
            # a 404 reponse.

            if request.method in ('GET', 'OPTIONS', 'HEAD'):
                # Read permissions already checked and failed, no need
                # to make another lookup.
                raise Http404

            read_perms = self.get_required_object_permissions('GET', model_cls)
            if not user.has_perms(read_perms, obj):
                raise Http404

            # Has read permissions.
            return False

        return True


class TokenHasReadWriteScope(BasePermission):
    """
    The request is authenticated as a user and the token used has the right scope
    """

    def has_permission(self, request, view):
        token = request.auth
        read_only = request.method in SAFE_METHODS

        if not token:
            return False

        if hasattr(token, 'resource'):  # OAuth 1
            return read_only or not request.auth.resource.is_readonly
        elif hasattr(token, 'scope'):  # OAuth 2
            required = oauth2_constants.READ if read_only else oauth2_constants.WRITE
            return oauth2_provider_scope.check(required, request.auth.scope)

        assert False, ('TokenHasReadWriteScope requires either the'
        '`OAuthAuthentication` or `OAuth2Authentication` authentication '
        'class to be used.')
