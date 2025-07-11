"""
django-guardian helper functions.

Functions defined within this module should be considered as django-guardian's
internal functionality. They are **not** guaranteed to be stable - which means
they actual input parameters/output type may change in future releases.
"""
import logging
import os
from itertools import chain

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME, get_user_model
from django.contrib.auth.models import AnonymousUser, Group
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db.models import Model, QuerySet
from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import render
from guardian.conf import settings as guardian_settings
from guardian.ctypes import get_content_type
from guardian.exceptions import NotUserNorGroup

logger = logging.getLogger(__name__)
abspath = lambda *p: os.path.abspath(os.path.join(*p))


def get_anonymous_user():
    """
    Returns ``User`` instance (not ``AnonymousUser``) depending on
    ``ANONYMOUS_USER_NAME`` configuration.
    """
    User = get_user_model()
    lookup = {User.USERNAME_FIELD: guardian_settings.ANONYMOUS_USER_NAME}
    return User.objects.get(**lookup)


def get_identity(identity):
    """
    Returns (user_obj, None) or (None, group_obj) tuple depending on what is
    given. Also accepts AnonymousUser instance but would return ``User``
    instead - it is convenient and needed for authorization backend to support
    anonymous users.

    :param identity: either ``User`` or ``Group`` instance

    :raises ``NotUserNorGroup``: if cannot return proper identity instance

    **Examples**::

       >>> from django.contrib.auth.models import User
       >>> user = User.objects.create(username='joe')
       >>> get_identity(user)
       (<User: joe>, None)

       >>> group = Group.objects.create(name='users')
       >>> get_identity(group)
       (None, <Group: users>)

       >>> anon = AnonymousUser()
       >>> get_identity(anon)
       (<User: AnonymousUser>, None)

       >>> get_identity("not instance")
       ...
       NotUserNorGroup: User/AnonymousUser or Group instance is required (got )

    """
    if isinstance(identity, AnonymousUser):
        identity = get_anonymous_user()

    # get identity from queryset model type
    if isinstance(identity, QuerySet):
        identity_model_type = identity.model
        if identity_model_type == get_user_model():
            return identity, None
        elif identity_model_type == Group:
            return None, identity

    # get identity from first element in list
    if isinstance(identity, list) and isinstance(identity[0], get_user_model()):
        return identity, None
    if isinstance(identity, list) and isinstance(identity[0], Group):
        return None, identity

    if isinstance(identity, get_user_model()):
        return identity, None
    if isinstance(identity, Group):
        return None, identity

    raise NotUserNorGroup("User/AnonymousUser or Group instance is required "
                          "(got %s)" % identity)


def get_40x_or_None(request, perms, obj=None, login_url=None,
                    redirect_field_name=None, return_403=False,
                    return_404=False, accept_global_perms=False,
                    any_perm=False):
    login_url = login_url or settings.LOGIN_URL
    redirect_field_name = redirect_field_name or REDIRECT_FIELD_NAME

    # Handles both original and with object provided permission check
    # as ``obj`` defaults to None

    has_permissions = False
    # global perms check first (if accept_global_perms)
    if accept_global_perms:
        has_permissions = all(request.user.has_perm(perm) for perm in perms)
    # if still no permission granted, try obj perms
    if not has_permissions:
        if any_perm:
            has_permissions = any(request.user.has_perm(perm, obj)
                                  for perm in perms)
        else:
            has_permissions = all(request.user.has_perm(perm, obj)
                                  for perm in perms)

    if not has_permissions:
        if return_403:
            if guardian_settings.RENDER_403:
                response = render(request, guardian_settings.TEMPLATE_403)
                response.status_code = 403
                return response
            elif guardian_settings.RAISE_403:
                raise PermissionDenied
            return HttpResponseForbidden()
        if return_404:
            if guardian_settings.RENDER_404:
                response = render(request, guardian_settings.TEMPLATE_404)
                response.status_code = 404
                return response
            elif guardian_settings.RAISE_404:
                raise ObjectDoesNotExist
            return HttpResponseNotFound()
        else:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path(),
                                     login_url,
                                     redirect_field_name)


from django.apps import apps as django_apps
from django.core.exceptions import ImproperlyConfigured

def get_obj_perm_model_by_conf(setting_name):
    """
    Return the model that matches the guardian settings.
    """
    try:
        setting_value = getattr(guardian_settings, setting_name)
        return django_apps.get_model(setting_value, require_ready=False)
    except ValueError as e:
        raise ImproperlyConfigured("{} must be of the form 'app_label.model_name'".format(setting_value)) from e
    except LookupError as e:
        raise ImproperlyConfigured(
            "{} refers to model '{}' that has not been installed".format(setting_name, setting_value)
        ) from e


def clean_orphan_obj_perms():
    """
    Seeks and removes all object permissions entries pointing at non-existing
    targets.

    Returns number of removed objects.
    """
    UserObjectPermission = get_user_obj_perms_model()
    GroupObjectPermission = get_group_obj_perms_model()

    deleted = 0
    # TODO: optimise
    for perm in chain(UserObjectPermission.objects.all().iterator(),
                      GroupObjectPermission.objects.all().iterator()):
        if perm.content_object is None:
            logger.debug("Removing %s (pk=%d)" % (perm, perm.pk))
            perm.delete()
            deleted += 1
    logger.info("Total removed orphan object permissions instances: %d" %
                deleted)
    return deleted


# TODO: should raise error when multiple UserObjectPermission direct relations
# are defined

def get_obj_perms_model(obj, base_cls, generic_cls):
    """
    Return the matching object permission model for the obj class
    Defaults to returning the generic object permission when
    no direct foreignkey is defined or obj is None
    """
    # Default to the generic object permission model
    # when None obj is provided
    if obj is None:
        return generic_cls

    if isinstance(obj, Model):
        obj = obj.__class__

    fields = (f for f in obj._meta.get_fields()
                if (f.one_to_many or f.one_to_one) and f.auto_created)

    for attr in fields:
        model = getattr(attr, 'related_model', None)
        if (model and issubclass(model, base_cls) and
                model is not generic_cls and getattr(model, 'enabled', True)):
            # if model is generic one it would be returned anyway
            if not model.objects.is_generic():
                # make sure that content_object's content_type is same as
                # the one of given obj
                fk = model._meta.get_field('content_object')
                if get_content_type(obj) == get_content_type(fk.remote_field.model):
                    return model
    return generic_cls


def get_user_obj_perms_model(obj = None):
    """
    Returns model class that connects given ``obj`` and User class.
    If obj is not specified, then user generic object permission model
    returned is determined by the guardian setting 'USER_OBJ_PERMS_MODEL'
    """
    from guardian.models import UserObjectPermissionBase
    UserObjectPermission = get_obj_perm_model_by_conf('USER_OBJ_PERMS_MODEL')
    return get_obj_perms_model(obj, UserObjectPermissionBase, UserObjectPermission)


def get_group_obj_perms_model(obj = None):
    """
    Returns model class that connects given ``obj`` and Group class.
    If obj is not specified, then group generic object permission model
    returned is determined byt the guardian setting 'GROUP_OBJ_PERMS_MODEL'.
    """
    from guardian.models import GroupObjectPermissionBase
    GroupObjectPermission = get_obj_perm_model_by_conf('GROUP_OBJ_PERMS_MODEL')
    return get_obj_perms_model(obj, GroupObjectPermissionBase, GroupObjectPermission)


def evict_obj_perms_cache(obj):
    if hasattr(obj, '_guardian_perms_cache'):
        delattr(obj, '_guardian_perms_cache')
        return True
    return False
