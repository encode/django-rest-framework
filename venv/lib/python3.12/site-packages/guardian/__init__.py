"""
Implementation of per object permissions for Django.
"""
from . import checks
import django

if django.VERSION < (3, 2):
    default_app_config = 'guardian.apps.GuardianConfig'

# PEP 396: The __version__ attribute's value SHOULD be a string.
__version__ = '2.4.0'

# Compatibility to eg. django-rest-framework
VERSION = tuple(int(x) for x in __version__.split('.')[:3])


def get_version():
    return __version__


def monkey_patch_user():
    from django.contrib.auth import get_user_model
    from .utils import get_anonymous_user, evict_obj_perms_cache
    from .utils import get_user_obj_perms_model
    UserObjectPermission = get_user_obj_perms_model()
    User = get_user_model()
    # Prototype User and Group methods
    setattr(User, 'get_anonymous', staticmethod(lambda: get_anonymous_user()))
    setattr(User, 'add_obj_perm',
            lambda self, perm, obj: UserObjectPermission.objects.assign_perm(perm, self, obj))
    setattr(User, 'del_obj_perm',
            lambda self, perm, obj: UserObjectPermission.objects.remove_perm(perm, self, obj))
    setattr(User, 'evict_obj_perms_cache', evict_obj_perms_cache)


def monkey_patch_group():
    from django.contrib.auth.models import Group, Permission
    from .utils import get_group_obj_perms_model
    GroupObjectPermission = get_group_obj_perms_model()
    # Prototype Group methods
    setattr(Group, 'add_obj_perm',
            lambda self, perm, obj: GroupObjectPermission.objects.assign_perm(perm, self, obj))
    setattr(Group, 'del_obj_perm',
            lambda self, perm, obj: GroupObjectPermission.objects.remove_perm(perm, self, obj))
