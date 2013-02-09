"""
Force import of all modules in this package in order to get the standard test
runner to pick up the tests.  Yowzers.
"""
from __future__ import unicode_literals
import os

modules = [filename.rsplit('.', 1)[0]
           for filename in os.listdir(os.path.dirname(__file__))
           if filename.endswith('.py') and not filename.startswith('_')]
__test__ = dict()

for module in modules:
    exec("from rest_framework.tests.%s import *" % module)
