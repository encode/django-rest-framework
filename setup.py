#!/usr/bin/env/python
# -*- coding: utf-8 -*-

from setuptools import setup

import os, re

path = os.path.join(os.path.dirname(__file__), 'djangorestframework', '__init__.py')
init_py = open(path).read()
VERSION = re.match("__version__ = '([^']+)'", init_py).group(1)

setup(
    name = 'djangorestframework',
    version = VERSION,
    url = 'http://django-rest-framework.org',
    download_url = 'http://pypi.python.org/pypi/djangorestframework/',
    license = 'BSD',
    description = 'A lightweight REST framework for Django.',
    author = 'Tom Christie',
    author_email = 'tom@tomchristie.com',
    packages = ['djangorestframework',
                'djangorestframework.templatetags',
                'djangorestframework.tests',
                'djangorestframework.runtests',
                'djangorestframework.utils'],
    package_dir={'djangorestframework': 'djangorestframework'},
    package_data = {'djangorestframework': ['templates/*', 'static/*']},
    test_suite = 'djangorestframework.runtests.runcoverage.main',
    install_requires=['URLObject>=0.6.0'],
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ]
)
