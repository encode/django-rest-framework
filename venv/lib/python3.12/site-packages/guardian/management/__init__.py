from django.contrib.auth import get_user_model
from django.db.models import signals
from django.utils.module_loading import import_string
from django.db import router
from guardian.conf import settings as guardian_settings


def get_init_anonymous_user(User):
    """
    Returns User model instance that would be referenced by guardian when
    permissions are checked against users that haven't signed into the system.

    :param User: User model - result of ``django.contrib.auth.get_user_model``.
    """
    kwargs = {
        User.USERNAME_FIELD: guardian_settings.ANONYMOUS_USER_NAME
    }
    user = User(**kwargs)
    user.set_unusable_password()
    return user


def create_anonymous_user(sender, **kwargs):
    """
    Creates anonymous User instance with id and username from settings.
    """
    User = get_user_model()
    if not router.allow_migrate_model(kwargs['using'], User):
        return
    try:
        lookup = {User.USERNAME_FIELD: guardian_settings.ANONYMOUS_USER_NAME}
        User.objects.using(kwargs['using']).get(**lookup)
    except User.DoesNotExist:
        retrieve_anonymous_function = import_string(
            guardian_settings.GET_INIT_ANONYMOUS_USER)
        user = retrieve_anonymous_function(User)
        user.save(using=kwargs['using'])

# Only create an anonymous user if support is enabled.
if guardian_settings.ANONYMOUS_USER_NAME is not None:
    from django.apps import apps
    guardian_app = apps.get_app_config('guardian')
    signals.post_migrate.connect(create_anonymous_user, sender=guardian_app,
                                 dispatch_uid="guardian.management.create_anonymous_user")
