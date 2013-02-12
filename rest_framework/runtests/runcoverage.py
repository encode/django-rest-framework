#!/usr/bin/env python
"""
Useful tool to run the test suite for rest_framework and generate a coverage report.
"""

# http://ericholscher.com/blog/2009/jun/29/enable-setuppy-test-your-django-apps/
# http://www.travisswicegood.com/2010/01/17/django-virtualenv-pip-and-fabric/
# http://code.djangoproject.com/svn/django/trunk/tests/runtests.py
import os
import sys

# fix sys path so we don't need to setup PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))
os.environ['DJANGO_SETTINGS_MODULE'] = 'rest_framework.runtests.settings'

from coverage import coverage


def main():
    """Run the tests for rest_framework and generate a coverage report."""

    cov = coverage()
    cov.erase()
    cov.start()

    from django.conf import settings
    from django.test.utils import get_runner
    TestRunner = get_runner(settings)

    if hasattr(TestRunner, 'func_name'):
        # Pre 1.2 test runners were just functions,
        # and did not support the 'failfast' option.
        import warnings
        warnings.warn(
            'Function-based test runners are deprecated. Test runners should be classes with a run_tests() method.',
            DeprecationWarning
        )
        failures = TestRunner(['tests'])
    else:
        test_runner = TestRunner()
        failures = test_runner.run_tests(['tests'])
    cov.stop()

    # Discover the list of all modules that we should test coverage for
    import rest_framework

    project_dir = os.path.dirname(rest_framework.__file__)
    cov_files = []

    for (path, dirs, files) in os.walk(project_dir):
        # Drop tests and runtests directories from the test coverage report
        if os.path.basename(path) in ['tests', 'runtests', 'migrations']:
            continue

        # Drop the compat and six modules from coverage, since we're not interested in the coverage
        # of modules which are specifically for resolving environment dependant imports.
        # (Because we'll end up getting different coverage reports for it for each environment)
        if 'compat.py' in files:
            files.remove('compat.py')

        if 'six.py' in files:
            files.remove('six.py')

        # Same applies to template tags module.
        # This module has to include branching on Django versions,
        # so it's never possible for it to have full coverage.
        if 'rest_framework.py' in files:
            files.remove('rest_framework.py')

        cov_files.extend([os.path.join(path, file) for file in files if file.endswith('.py')])

    cov.report(cov_files)
    if '--html' in sys.argv:
        cov.html_report(cov_files, directory='coverage')
    sys.exit(failures)

if __name__ == '__main__':
    main()
