from django.core.checks import Tags, Warning, register


@register(Tags.compatibility)
def pagination_system_check(app_configs, **kwargs):
    errors = []
    # Use of default page size setting requires a default Paginator class
    from rest_framework.settings import api_settings
    if api_settings.PAGE_SIZE and not api_settings.DEFAULT_PAGINATION_CLASS:
        errors.append(
            Warning(
                "You have specified a default `PAGE_SIZE` pagination rest_framework setting,"
                "without specifying also a `DEFAULT_PAGINATION_CLASS`.",
                hint="The prior version of rest_framework defaulted this setting to "
                "`PageNumberPagination` however pagination defaults to disabled now.  "
                "Consider specifying `DEFAULT_PAGINATION_CLASS` explicitly for your project, "
                "unless you specify individual pagination_class values on specific view classes.",
            )
        )
    return errors
