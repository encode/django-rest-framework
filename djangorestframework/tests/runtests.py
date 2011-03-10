'''
Created on Mar 10, 2011

@author: tomchristie
'''
# http://ericholscher.com/blog/2009/jun/29/enable-setuppy-test-your-django-apps/
# http://www.travisswicegood.com/2010/01/17/django-virtualenv-pip-and-fabric/
from django.conf import settings
from django.core.management import call_command

def runtests():
    settings.configure(
        INSTALLED_APPS=(
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.sites',
            'django.contrib.messages',
            'djangorestframework',
        ),
        ROOT_URLCONF='djangorestframework.tests.urls',
        # Django replaces this, but it still wants it. *shrugs*
        DATABASE_ENGINE='sqlite3'
    )
    call_command('test', 'djangorestframework')


if __name__ == '__main__':
    runtests()
