from django.conf import settings

# django-crispy-forms is optional
try:
    import crispy_forms
except ImportError:
    crispy_forms = None


def is_crispy():
    return "crispy_forms" in settings.INSTALLED_APPS and crispy_forms
