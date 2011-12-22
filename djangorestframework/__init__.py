__version__ = '0.2.3'

VERSION = __version__  # synonym

from djangorestframework.builtins import Api

import imp

__all__ = ('autodiscover','api', '__version__', 'VERSION')

api = Api()

def autodiscover():
    """
    Auto-discover INSTALLED_APPS api.py modules and fail silently when
    not present. This forces an import on them to register any api entries they
    may want.
    """
    import copy
    from django.conf import settings
    from django.utils.importlib import import_module

    for app in settings.INSTALLED_APPS:
        # Attempt to import the app's api module.
        before_import_registry = copy.copy(api._registry)
        try:
            import_module('%s.api' % app)
        except:
            # Reset the model registry to the state before the last import as
            # this import will have to reoccur on the next request and this
            # could raise NotRegistered and AlreadyRegistered exceptions
            # (see https://code.djangoproject.com/ticket/8245)
            api._registry = before_import_registry
