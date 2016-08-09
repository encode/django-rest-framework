from importlib import import_module

from django.apps import AppConfig
from django.conf import settings
from django.utils.translation import ugettext_lazy as _


class RestFrameworkConfig(AppConfig):
    name = 'rest_framework'
    verbose_name = _("REST Framework")

    def ready(self):
        """
        Try to auto-import any modules in INSTALLED_APPS.

        This lets us evaluate all of the @router.route('...') calls.
        """
        for app in settings.INSTALLED_APPS:
            for mod_name in ['api']:
                try:
                    import_module('%s.%s' % (app, mod_name))
                except ImportError:
                    pass
