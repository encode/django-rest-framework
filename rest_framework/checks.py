from django.core.checks import Error, Tags, Warning, register


@register(Tags.compatibility)
def pagination_system_check(app_configs, **kwargs):
    errors = []
    # Use of default page size setting requires a default Paginator class
    from rest_framework.settings import api_settings
    if api_settings.PAGE_SIZE and not api_settings.DEFAULT_PAGINATION_CLASS:
        errors.append(
            Warning(
                "You have specified a default PAGE_SIZE pagination rest_framework setting, "
                "without specifying also a DEFAULT_PAGINATION_CLASS.",
                hint="The default for DEFAULT_PAGINATION_CLASS is None. "
                     "In previous versions this was PageNumberPagination. "
                     "If you wish to define PAGE_SIZE globally whilst defining "
                     "pagination_class on a per-view basis you may silence this check.",
                id="rest_framework.W001"
            )
        )
    return errors


@register(Tags.compatibility)
def www_authenticate_behavior_setting_check(app_configs, **kwargs):
    errors = []
    # WWW_AUTHENTICATE_BEHAVIOR setting must be 'first' or 'all'
    from rest_framework.settings import api_settings
    setting = api_settings.WWW_AUTHENTICATE_BEHAVIOR
    if setting not in ['first', 'all']:
        errors.append(
            Error(
                "The rest_framework setting WWW_AUTHENTICATE_BEHAVIOR must be either "
                f"'first' or 'all' (it is currently set to '{setting}').",
                hint="Set WWW_AUTHENTICATE_BEHAVIOR to either 'first' or 'all', "
                     "or leave it unset (the default value is 'first').",
                id="rest_framework.E001",
            )
        )
    return errors
