from django.core.checks import Tags, Warning, register


@register(Tags.compatibility)
def pagination_system_check(app_configs, **kwargs):
    errors = []
    # Use of default page size setting requires a default Paginator class
    from rest_framework.settings import api_settings
    if api_settings.PAGE_SIZE and not api_settings.DEFAULT_PAGINATION_CLASS:
        errors.append(
            Warning(
                "You have specified a default PAGE_SIZE pagination rest_framework setting,"
                "without specifying also a DEFAULT_PAGINATION_CLASS.",
                hint="The default for DEFAULT_PAGINATION_CLASS is None. "
                     "In previous versions this was PageNumberPagination",
            )
        )
    return errors
