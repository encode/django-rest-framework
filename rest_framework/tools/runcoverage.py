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
os.environ['DJANGO_SETTINGS_MODULE'] = 'rest_framework.tests.settings'

from django.conf import settings

try:
    from coverage import coverage
except ImportError:
    print("Coverage is not installed. Aborting...")
    exit(1)


def report(cov, cov_files):
    pc = cov.report(cov_files)

    if '--html' in sys.argv:
        cov.html_report(cov_files, directory='coverage')

    if '--xml' in sys.argv:
        cov.xml_report(cov_files, outfile='../../coverage.xml')

    return pc


def prepare_report(project_dir):
    cov_files = []

    for (path, dirs, files) in os.walk(project_dir):
        # Drop tests and runtests directories from the test coverage report
        if os.path.basename(path) in ['tests', 'runtests', 'migrations']:
            continue

        # Drop the compat module from coverage, since we're not interested in the coverage
        # of a module which is specifically for resolving environment dependant imports.
        # (Because we'll end up getting different coverage reports for it for each environment)
        if 'compat.py' in files:
            files.remove('compat.py')

        # Same applies to template tags module.
        # This module has to include branching on Django versions,
        # so it's never possible for it to have full coverage.
        if 'rest_framework.py' in files:
            files.remove('rest_framework.py')

        cov_files.extend([os.path.join(
            path, file) for file in files if file.endswith('.py')])

    return cov_files


def run_tests(app):
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
        failures = TestRunner([app])
    else:
        test_runner = TestRunner()
        failures = test_runner.run_tests([app])
    return failures


def main():
    """Run the tests for rest_framework and generate a coverage report."""

    cov = coverage(data_file=".coverage", branch=True)
    cov.erase()
    cov.start()

    failures = run_tests('rest_framework')
    cov.stop()

    # Discover the list of all modules that we should test coverage for
    import rest_framework

    project_dir = os.path.dirname(rest_framework.__file__)
    cov_files = prepare_report(project_dir)

    report(cov, cov_files)
    pc = report(cov, cov_files)
    if failures != 0:
        sys.exit(failures)

    if pc < settings.CODE_COVERAGE_THRESHOLD:
        sys.exit(pc)

    sys.exit(0)

if __name__ == '__main__':
    main()
