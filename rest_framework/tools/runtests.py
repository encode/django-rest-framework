#!/usr/bin/env python
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "rest_framework.tests.settings")

from django.core.management import execute_from_command_line

sys.argv.append(1, 'test')
execute_from_command_line(sys.argv)
