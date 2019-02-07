import os
import coverage
import shutil
import subprocess
import sys
import tempfile

import django
from django import conf
from django.conf import settings
from django.test import TestCase


class BaseTestProjectTestsCase(TestCase):

    def setUp(self):
        tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(tmpdir.cleanup)
        self.test_dir = os.path.join(tmpdir.name, 'test_project')
        os.mkdir(self.test_dir)
        with open(os.path.join(self.test_dir, '__init__.py'), 'w'):
            pass

    def write_settings(self, filename, apps=[], sdict={}):
        settings_file_path = os.path.join(self.test_dir, filename)

        with open(settings_file_path, 'w') as settings_file:
            exports = [
                'DATABASES',
                'SECRET_KEY',
                'ROOT_URLCONF',
            ]
            for s in exports:
                if hasattr(settings, s):
                    o = getattr(settings, s)
                    if not isinstance(o, (dict, tuple, list)):
                        o = "'%s'" % o
                    settings_file.write("%s = %s\n" % (s, sdict.pop(s, o)))

            installed_apps = [
                'django.contrib.auth',
                'django.contrib.contenttypes',
                'rest_framework'
            ]
            installed_apps.extend(apps)

            settings_file.write("INSTALLED_APPS = %s\n" % installed_apps)

            if sdict:
                for k, v in sdict.items():
                    settings_file.write("%s = %s\n" % (k, v))

    def run_test(self, script, args, settings_file=None):
        base_dir = os.path.dirname(self.test_dir)
        tests_dir = os.path.dirname(os.path.dirname(__file__))
        django_dir = os.path.dirname(tests_dir)
        ext_backend_base_dirs = self._ext_backend_paths()

        # Define a temporary environment for the subprocess
        test_environ = os.environ.copy()

        # Set the test environment
        if settings_file:
            test_environ['DJANGO_SETTINGS_MODULE'] = settings_file
        elif 'DJANGO_SETTINGS_MODULE' in test_environ:
            del test_environ['DJANGO_SETTINGS_MODULE']
        python_path = [base_dir, django_dir, tests_dir]
        python_path.extend(ext_backend_base_dirs)
        test_environ['PYTHONPATH'] = os.pathsep.join(python_path)
        test_environ['PYTHONWARNINGS'] = ''

        coverage.process_startup()
        return subprocess.Popen(
            [sys.executable, script] + args,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=self.test_dir,
            env=test_environ, universal_newlines=True,
        ).communicate()

    def run_django_admin(self, args, settings_file=None):
        script_dir = os.path.abspath(os.path.join(os.path.dirname(django.__file__), 'bin'))
        return self.run_test(os.path.join(script_dir, 'django-admin.py'), args, settings_file)

    def run_manage(self, args, settings_file=None, configured_settings=False):
        template_manage_py = (
            os.path.join(os.path.dirname(__file__), 'configured_settings_manage.py')
            if configured_settings else
            os.path.join(os.path.dirname(conf.__file__), 'project_template', 'manage.py-tpl')
        )
        test_manage_py = os.path.join(self.test_dir, 'manage.py')
        shutil.copyfile(template_manage_py, test_manage_py)

        with open(test_manage_py) as fp:
            manage_py_contents = fp.read()
        manage_py_contents = manage_py_contents.replace(
            "{{ project_name }}", "test_project")
        with open(test_manage_py, 'w') as fp:
            fp.write(manage_py_contents)

        return self.run_test('./manage.py', args, settings_file)

    def create_mysite_app(self):
        self.run_django_admin(['startapp', 'mysite'], 'settings.py')
        self.app_path = os.path.join(self.test_dir, 'mysite')
        self._prepare_models()
        self._prepare_serializers()
        self._prepare_views()
        self.write_settings('settings.py', apps=['mysite'])
        self._create_urls()
        self.write_settings('settings.py', apps=['mysite'],
                            sdict={'ROOT_URLCONF': "'urls'"})

    def _ext_backend_paths(self):
        """
        Returns the paths for any external backend packages.
        """
        paths = []
        for backend in settings.DATABASES.values():
            package = backend['ENGINE'].split('.')[0]
            if package != 'django':
                backend_pkg = __import__(package)
                backend_dir = os.path.dirname(backend_pkg.__file__)
                paths.append(os.path.dirname(backend_dir))
        return paths

    def _create_urls(self):
        with open(os.path.join(self.test_dir, 'urls.py'), 'w') as f:
            f.write("""from django.urls import include, path

from rest_framework import routers

from mysite import views

router = routers.DefaultRouter()
router.register(r'sample', views.SampleViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
""")

    def _prepare_models(self):
        with open(os.path.join(self.app_path, 'models.py'), 'w') as f:
            f.write("""from django.db import models


class Sample(models.Model):
    pass
""")

    def _prepare_serializers(self):
        with open(os.path.join(self.app_path, 'serializers.py'), 'w') as f:
            f.write("""from rest_framework import serializers

from .models import Sample


class SampleSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Sample
        fields = '__all__'
""")

    def _prepare_views(self):
        with open(os.path.join(self.app_path, 'views.py'), 'w') as f:
            f.write('''from rest_framework import viewsets

from .models import Sample
from .serializers import SampleSerializer


class SampleViewSet(viewsets.ModelViewSet):
    """Test API description."""

    queryset = Sample.objects.all()
    serializer_class = SampleSerializer
''')


class GenerateSchemaTests(BaseTestProjectTestsCase):
    """Tests for management command generateschema."""

    def setUp(self):  # noqa
        super(GenerateSchemaTests, self).setUp()
        self.write_settings('settings.py')
        self.create_mysite_app()

    def test_should_r_custom_title_url_and_description(self):
        expected_nodes = """description: Sample description
title: Sample API
url: http://api.sample.com
"""
        out, err = self.run_manage(['generateschema', '--title=Sample API',
                                    '--url=http://api.sample.com',
                                    '--description=Sample description'])

        self.assertEqual(err, '')
        for node in expected_nodes.splitlines():
            self.assertIn(node, out)

    def test_should_render_default_schema(self):
        expected_out = """info:
  description: ''
  title: ''
  version: ''
openapi: 3.0.0
paths:
  /sample/:
    get:
      description: Test API description.
      operationId: sample_list
      tags:
      - sample
    post:
      description: Test API description.
      operationId: sample_create
      tags:
      - sample
  /sample/{id}/:
    delete:
      description: Test API description.
      operationId: sample_delete
      parameters:
      - in: path
        name: id
        required: true
        schema:
          description: A unique integer value identifying this sample.
          title: ID
          type: integer
      tags:
      - sample
    get:
      description: Test API description.
      operationId: sample_read
      parameters:
      - in: path
        name: id
        required: true
        schema:
          description: A unique integer value identifying this sample.
          title: ID
          type: integer
      tags:
      - sample
    patch:
      description: Test API description.
      operationId: sample_partial_update
      parameters:
      - in: path
        name: id
        required: true
        schema:
          description: A unique integer value identifying this sample.
          title: ID
          type: integer
      tags:
      - sample
    put:
      description: Test API description.
      operationId: sample_update
      parameters:
      - in: path
        name: id
        required: true
        schema:
          description: A unique integer value identifying this sample.
          title: ID
          type: integer
      tags:
      - sample
servers:
- url: ''
"""

        out, err = self.run_manage(['generateschema'])

        self.assertEqual(err, '')
        self.assertIn(out, expected_out)

    def test_should_render_openapi_json_schema(self):
        expected_out = """{
    "openapi": "3.0.0",
    "info": {
        "version": "",
        "title": "",
        "description": ""
    },
    "servers": [
        {
            "url": ""
        }
    ],
    "paths": {
        "/sample/": {
            "get": {
                "operationId": "sample_list",
                "description": "Test API description.",
                "tags": [
                    "sample"
                ]
            },
            "post": {
                "operationId": "sample_create",
                "description": "Test API description.",
                "tags": [
                    "sample"
                ]
            }
        },
        "/sample/{id}/": {
            "get": {
                "operationId": "sample_read",
                "description": "Test API description.",
                "parameters": [
                    {
                        "name": "id",
                        "in": "path",
                        "required": true,
                        "schema": {
                            "type": "integer",
                            "title": "ID",
                            "description": "A unique integer value identifying this sample."
                        }
                    }
                ],
                "tags": [
                    "sample"
                ]
            },
            "put": {
                "operationId": "sample_update",
                "description": "Test API description.",
                "parameters": [
                    {
                        "name": "id",
                        "in": "path",
                        "required": true,
                        "schema": {
                            "type": "integer",
                            "title": "ID",
                            "description": "A unique integer value identifying this sample."
                        }
                    }
                ],
                "tags": [
                    "sample"
                ]
            },
            "patch": {
                "operationId": "sample_partial_update",
                "description": "Test API description.",
                "parameters": [
                    {
                        "name": "id",
                        "in": "path",
                        "required": true,
                        "schema": {
                            "type": "integer",
                            "title": "ID",
                            "description": "A unique integer value identifying this sample."
                        }
                    }
                ],
                "tags": [
                    "sample"
                ]
            },
            "delete": {
                "operationId": "sample_delete",
                "description": "Test API description.",
                "parameters": [
                    {
                        "name": "id",
                        "in": "path",
                        "required": true,
                        "schema": {
                            "type": "integer",
                            "title": "ID",
                            "description": "A unique integer value identifying this sample."
                        }
                    }
                ],
                "tags": [
                    "sample"
                ]
            }
        }
    }
}
"""

        out, err = self.run_manage(['generateschema', '--format=openapi-json'])

        self.assertEqual(err, '')
        self.assertIn(out, expected_out)

    def test_should_render_corejson_schema(self):
        expected_out = """{"_type":"document","sample":{"list":{"_type":"link","url":"/sample/","action":"get","description":"Test API description."},"create":{"_type":"link","url":"/sample/","action":"post","description":"Test API description."},"read":{"_type":"link","url":"/sample/{id}/","action":"get","description":"Test API description.","fields":[{"name":"id","required":true,"location":"path","schema":{"_type":"integer","title":"ID","description":"A unique integer value identifying this sample."}}]},"update":{"_type":"link","url":"/sample/{id}/","action":"put","description":"Test API description.","fields":[{"name":"id","required":true,"location":"path","schema":{"_type":"integer","title":"ID","description":"A unique integer value identifying this sample."}}]},"partial_update":{"_type":"link","url":"/sample/{id}/","action":"patch","description":"Test API description.","fields":[{"name":"id","required":true,"location":"path","schema":{"_type":"integer","title":"ID","description":"A unique integer value identifying this sample."}}]},"delete":{"_type":"link","url":"/sample/{id}/","action":"delete","description":"Test API description.","fields":[{"name":"id","required":true,"location":"path","schema":{"_type":"integer","title":"ID","description":"A unique integer value identifying this sample."}}]}}}"""  # noqa

        out, err = self.run_manage(['generateschema', '--format=corejson'])

        self.assertEqual(err, '')
        self.assertJSONEqual(out, expected_out)
