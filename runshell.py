#! /usr/bin/env python
import django
import sys
from django.core.management import execute_from_command_line


def runshell():
    from tests import conftest
    conftest.pytest_configure()

    execute_from_command_line(
        sys.argv[:1] +
        ['migrate', '--noinput', '-v', '0'] +
        (['--run-syncdb'] if django.VERSION >= (1, 9) else []))

    argv = sys.argv[:1] + ['shell'] + sys.argv[1:]
    execute_from_command_line(argv)


if __name__ == '__main__':
    runshell()
