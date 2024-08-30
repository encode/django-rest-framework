from django.core.exceptions import ImproperlyConfigured

from rest_framework.settings import api_settings
from rest_framework.views import APIView

try:
    from django.contrib.auth.middleware import \
        LoginRequiredMiddleware as DjangoLoginRequiredMiddleware
except ImportError:
    DjangoLoginRequiredMiddleware = None


if DjangoLoginRequiredMiddleware:
    class LoginRequiredMiddleware(DjangoLoginRequiredMiddleware):
        def process_view(self, request, view_func, view_args, view_kwargs):
            if (
                hasattr(view_func, "cls")
                and issubclass(view_func.cls, APIView)
            ):
                if 'rest_framework.permissions.AllowAny' in api_settings.DEFAULT_PERMISSION_CLASSES:
                    raise ImproperlyConfigured(
                        "You cannot use 'rest_framework.permissions.AllowAny' in `DEFAULT_PERMISSION_CLASSES` "
                        "with `LoginRequiredMiddleware`."
                    )
                return None
            return super().process_view(request, view_func, view_args, view_kwargs)
