'''
Created on Mar 10, 2011

@author: tomchristie
'''
# http://ericholscher.com/blog/2009/jun/29/enable-setuppy-test-your-django-apps/
# http://www.travisswicegood.com/2010/01/17/django-virtualenv-pip-and-fabric/
# http://code.djangoproject.com/svn/django/trunk/tests/runtests.py
import os
import sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'djangorestframework.runtests.settings'

from django.conf import settings
from django.test.utils import get_runner

def main():
    TestRunner = get_runner(settings)

    if hasattr(TestRunner, 'func_name'):
        # Pre 1.2 test runners were just functions,
        # and did not support the 'failfast' option.
        import warnings
        warnings.warn(
            'Function-based test runners are deprecated. Test runners should be classes with a run_tests() method.',
            DeprecationWarning
        )
        failures = TestRunner(['djangorestframework'])
    else:
        test_runner = TestRunner()
        failures = test_runner.run_tests(['djangorestframework'])

    sys.exit(failures)

if __name__ == '__main__':
    main()
