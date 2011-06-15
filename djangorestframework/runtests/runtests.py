'''
Created on Mar 10, 2011

@author: tomchristie
'''
# http://ericholscher.com/blog/2009/jun/29/enable-setuppy-test-your-django-apps/
# http://www.travisswicegood.com/2010/01/17/django-virtualenv-pip-and-fabric/
# http://code.djangoproject.com/svn/django/trunk/tests/runtests.py
import os
import sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'djangorestframework.runtests.settings'

from django.conf import settings
from django.test.utils import get_runner

def usage():
    return """
    Usage: python runtests.py [UnitTestClass].[method]
    
    You can pass the Class name of the `UnitTestClass` you want to test.
    
    Append a method name if you only want to test a specific method of that class.
    """
    
def main():
    TestRunner = get_runner(settings)

    test_runner = TestRunner()
    if len(sys.argv) == 2:
        test_case = '.' + sys.argv[1]
    elif len(sys.argv) == 1:
        test_case = ''
    else:
        print usage()
        sys.exit(1)
    failures = test_runner.run_tests(['djangorestframework' + test_case])

    sys.exit(failures)

if __name__ == '__main__':
    main()
