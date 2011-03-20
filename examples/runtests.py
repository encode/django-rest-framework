import os
import sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'examples.settings'

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
        failures = TestRunner(None)
    else:
        test_runner = TestRunner()
        failures = test_runner.run_tests(None)

    sys.exit(failures)

if __name__ == '__main__':
    main()
