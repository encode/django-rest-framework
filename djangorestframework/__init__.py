
__version__ = '0.2.3'

VERSION = __version__  # synonym

from djangorestframework.builtins import DjangoRestFrameworkSite
from django.utils.importlib import import_module

import imp

__all__ = ('autodiscover','site', '__version__', 'VERSION')

api = DjangoRestFrameworkSite()

# A flag to tell us if autodiscover is running.  autodiscover will set this to
# True while running, and False when it finishes.
LOADING = False

def autodiscover():
    """
    Auto-discover INSTALLED_APPS api.py modules and fail silently when
    not present. This forces an import on them to register any api bits they
    may want.
    """

    # Bail out if autodiscover didn't finish loading from a previous call so
    # that we avoid running autodiscover again when the URLconf is loaded by
    # the exception handler to resolve the handler500 view.  This prevents an
    # admin.py module with errors from re-registering models and raising a
    # spurious AlreadyRegistered exception.
    global LOADING
    if LOADING:
        return
    LOADING = True

    from django.conf import settings

    for app in settings.INSTALLED_APPS:
        # For each app, we need to look for a api.py inside that
        # app's package. We can't use os.path here -- recall that modules may be
        # imported different ways (think zip files) -- so we need to get
        # the app's __path__ and look for api.py on that path.

        # Step 1: find out the app's __path__ Import errors here will (and
        # should) bubble up, but a missing __path__ (which is legal, but weird)
        # fails silently -- apps that do weird things with __path__ might
        # need to roll their own api registration.
        try:
            app_path = import_module(app).__path__
        except (AttributeError, ImportError):
            continue

        # Step 2: use imp.find_module to find the app's gargoyle_conditions.py.
        # For some # reason imp.find_module raises ImportError if the app can't
        # be found # but doesn't actually try to import the module. So skip this
        # app if its gargoyle.py doesn't exist
        try:
            imp.find_module('api', app_path)
        except ImportError:
            continue

        import_module("%s.api" % app)
        print 'aaaaaaaaaaaaa',app

    # autodiscover was successful, reset loading flag.
    LOADING = False
