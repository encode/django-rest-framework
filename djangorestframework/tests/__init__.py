"""Force import of all modules in this package in order to get the standard test runner to pick up the tests.  Yowzers."""
import os

modules = [filename.rsplit('.', 1)[0]
           for filename in os.listdir(os.path.dirname(__file__))
           if filename.endswith('.py') and not filename.startswith('_')]
__test__ = dict()

for module in modules:
    exec("from djangorestframework.tests.%s import __doc__ as module_doc" % module)
    exec("from djangorestframework.tests.%s import *" % module)
    __test__[module] = module_doc or ""

