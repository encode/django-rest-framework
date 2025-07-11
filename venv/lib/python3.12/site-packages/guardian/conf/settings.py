import warnings
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

try:
    ANONYMOUS_USER_NAME = settings.ANONYMOUS_USER_NAME
except AttributeError:
    try:
        ANONYMOUS_USER_NAME = settings.ANONYMOUS_DEFAULT_USERNAME_VALUE
        warnings.warn("The ANONYMOUS_DEFAULT_USERNAME_VALUE setting has been renamed to ANONYMOUS_USER_NAME.", DeprecationWarning)
    except AttributeError:
        ANONYMOUS_USER_NAME = "AnonymousUser"

RENDER_403 = getattr(settings, 'GUARDIAN_RENDER_403', False)
TEMPLATE_403 = getattr(settings, 'GUARDIAN_TEMPLATE_403', '403.html')
RAISE_403 = getattr(settings, 'GUARDIAN_RAISE_403', False)
RENDER_404 = getattr(settings, 'GUARDIAN_RENDER_404', False)
TEMPLATE_404 = getattr(settings, 'GUARDIAN_TEMPLATE_404', '404.html')
RAISE_404 = getattr(settings, 'GUARDIAN_RAISE_404', False)
GET_INIT_ANONYMOUS_USER = getattr(settings, 'GUARDIAN_GET_INIT_ANONYMOUS_USER',
                                  'guardian.management.get_init_anonymous_user')

MONKEY_PATCH = getattr(settings, 'GUARDIAN_MONKEY_PATCH', True)

GET_CONTENT_TYPE = getattr(settings, 'GUARDIAN_GET_CONTENT_TYPE', 'guardian.ctypes.get_default_content_type')

AUTO_PREFETCH = getattr(settings, 'GUARDIAN_AUTO_PREFETCH', False)

# Default to using guardian supplied generic object permission models
USER_OBJ_PERMS_MODEL = getattr(settings, 'GUARDIAN_USER_OBJ_PERMS_MODEL', 'guardian.UserObjectPermission')
GROUP_OBJ_PERMS_MODEL = getattr(settings, 'GUARDIAN_GROUP_OBJ_PERMS_MODEL', 'guardian.GroupObjectPermission')


def check_configuration():
    if RENDER_403 and RAISE_403:
        raise ImproperlyConfigured("Cannot use both GUARDIAN_RENDER_403 AND "
                                   "GUARDIAN_RAISE_403 - only one of this config may be True")

check_configuration()
