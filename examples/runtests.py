import os
import sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.conf import settings
from django.test.utils import get_runner
from coverage import coverage

def main():
    """Run the tests for the examples and generate a coverage report."""

    # Discover the list of all modules that we should test coverage for
    project_dir = os.path.dirname(__file__)
    cov_files = []
    for (path, dirs, files) in os.walk(project_dir):
        # Drop tests and runtests directories from the test coverage report
        if os.path.basename(path) == 'tests' or os.path.basename(path) == 'runtests':
            continue
        cov_files.extend([os.path.join(path, file) for file in files if file.endswith('.py')])
    TestRunner = get_runner(settings)

    cov = coverage()
    cov.erase()
    cov.start()
    if hasattr(TestRunner, 'func_name'):
        # Pre 1.2 test runners were just functions,
        # and did not support the 'failfast' option.
        import warnings
        warnings.warn(
            'Function-based test runners are deprecated. Test runners should be classes with a run_tests() method.',
            DeprecationWarning
        )
        failures = TestRunner(None)
    else:
        test_runner = TestRunner()
        failures = test_runner.run_tests(['blogpost', 'pygments_api'])

    cov.stop()
    cov.report(cov_files)
    cov.xml_report(cov_files)
    sys.exit(failures)

if __name__ == '__main__':
    main()
