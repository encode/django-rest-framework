#!/usr/bin/env python3
"""Basic script used to run django-admin checks in CI/tox."""
from django.conf import settings
from django.core.management import execute_from_command_line


if __name__ == "__main__":

    # Minimal settings required to check for migrations
    settings.configure(
        SECRET_KEY = "not very secret in checks either",
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:"
            }
        },
        INSTALLED_APPS = [
            'django.contrib.auth',
            'django.contrib.contenttypes',
            "rest_framework.authtoken"
        ]
    )

    print("Running basic Django system checks")
    execute_from_command_line(["manage.py", "check"])

    print("Checking for missing Django migrations")
    execute_from_command_line(["manage.py", "makemigrations", "--dry-run", "--verbosity=3", "--check"])
