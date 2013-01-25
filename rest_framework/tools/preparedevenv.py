"""
This script prepares all the required components in order to start developing django-rest-framework.
Installs virtualenv to the global site packages if it does not exist.
Installs all the necessary dependencies into a virtualenv at the specified path.

usage: ./preparedevenv.py [path-to-virtual-env]
"""

import subprocess
import os
import sys

def install(home):
    print("Installing dependencies into virtualenv at %s" % home)

    requirements_path = os.path.abspath(os.path.dirname(__file__))
    os.chdir(home)
    pip = './Scripts/pip-script.py'
    python = './Scripts/python'
    execfile('./Scripts/activate_this.py')
    subprocess.call(
        [python, pip, 'install', '-r', os.path.join(requirements_path, "../..", 'requirements.txt'), '-M'])
    subprocess.call(
        [python, pip, 'install', '-r', os.path.join(requirements_path, "../..", 'optionals.txt'), '-M'])
    subprocess.call(
        [python, pip, 'install', '-r', os.path.join(requirements_path, "../..", 'development.txt'), '-M'])


def after_install(home):
    install(home)

try:
    import pip
except ImportError:
    print("pip in not installed. Aborting...")
    exit(1)

def install_virtualenv():
    subprocess.call(['pip', 'install', 'virtualenv'])


def install_tox():
    subprocess.call(['pip', 'install', 'tox'])

try:
    import virtualenv
except ImportError:
    try:
        install_virtualenv()
    except:
        print("virtualenv installation has failed. Aborting...")
        exit(1)

install_tox()

from virtualenv import create_environment

if len(sys.argv) < 2:
    print("usage: ./preparedevenv.py [path-to-virtual-env]")
    exit(1)

path = sys.argv[1]
if not os.path.isdir(path):
    print("Creating virtualenv at %s" % path)
    create_environment(path, use_distribute=True, clear=True)
else:
    print("virtualenv at path %s seems to exist. Attempting to install dependencies." % path)

after_install(path)