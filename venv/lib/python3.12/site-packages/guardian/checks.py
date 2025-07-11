from django.conf import settings
from django.core.checks import register, Tags, Warning


# noinspection PyUnusedLocal
@register(Tags.compatibility)
def check_settings(app_configs, **kwargs):
    """ Check that settings are implemented properly
    :param app_configs: a list of apps to be checks or None for all
    :param kwargs: keyword arguments
    :return: a list of errors
    """
    checks = []
    if 'guardian.backends.ObjectPermissionBackend' not in settings.AUTHENTICATION_BACKENDS:
        msg = ("Guardian authentication backend is not hooked. You can add this in settings as eg: "
               "`AUTHENTICATION_BACKENDS = ('django.contrib.auth.backends.ModelBackend', "
               "'guardian.backends.ObjectPermissionBackend')`.")
        checks.append(Warning(msg, id='guardian.W001'))
    return checks
