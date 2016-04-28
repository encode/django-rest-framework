from __future__ import unicode_literals

import pytest
import sys

from rest_framework.compat import is_simple_callable


class TestFunctionSimplicityCheck:
    def get_good_cases(self):
        def simple():
            pass

        def simple_with_default(x=0):
            pass

        class SimpleMethods(object):
            def simple(self):
                pass

            def simple_with_default(self, x=0):
                pass

        return simple, simple_with_default, SimpleMethods().simple, SimpleMethods().simple_with_default

    def get_bad_cases(self):
        def positional(x):
            pass

        def many_positional_and_defaults(x, y, z=0):
            pass

        nofunc = 0

        class Callable:
            pass

        return positional, many_positional_and_defaults, nofunc, Callable

    def test_good_cases(self):
        for case in self.get_good_cases():
            assert is_simple_callable(case)

    def test_bad_cases(self):
        for case in self.get_bad_cases():
            assert not is_simple_callable(case)


if sys.version_info >= (3, 5):
    from tests.compat.test_compat_py35 import FunctionSimplicityCheckPy35Mixin

    class TestFunctionSimplicityCheckPy35(FunctionSimplicityCheckPy35Mixin, TestFunctionSimplicityCheck):
        pass
