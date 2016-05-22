from __future__ import unicode_literals

import functools
import os

from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.test import TestCase
from django.utils.translation import ugettext, ugettext_lazy as _

from rest_framework import (
    exceptions, metadata, serializers, status, versioning, views
)
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

request = Request(APIRequestFactory().options('/'))


class TestMetadata:
    def test_metadata(self):
        """
        OPTIONS requests to views should return a valid 200 response.
        """
        class ExampleView(views.APIView):
            """Example view."""
            pass

        view = ExampleView.as_view()
        response = view(request=request)
        expected = {
            'name': 'Example',
            'description': 'Example view.',
            'renders': [
                'application/json',
                'text/html'
            ],
            'parses': [
                'application/json',
                'application/x-www-form-urlencoded',
                'multipart/form-data'
            ]
        }
        assert response.status_code == status.HTTP_200_OK
        assert response.data == expected

    def test_none_metadata(self):
        """
        OPTIONS requests to views where `metadata_class = None` should raise
        a MethodNotAllowed exception, which will result in an HTTP 405 response.
        """
        class ExampleView(views.APIView):
            metadata_class = None

        view = ExampleView.as_view()
        response = view(request=request)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        assert response.data == {'detail': 'Method "OPTIONS" not allowed.'}

    def test_actions(self):
        """
        On generic views OPTIONS should return an 'actions' key with metadata
        on the fields that may be supplied to PUT and POST requests.
        """
        class NestedField(serializers.Serializer):
            a = serializers.IntegerField()
            b = serializers.IntegerField()

        class ExampleSerializer(serializers.Serializer):
            choice_field = serializers.ChoiceField(['red', 'green', 'blue'])
            integer_field = serializers.IntegerField(
                min_value=1, max_value=1000
            )
            char_field = serializers.CharField(
                required=False, min_length=3, max_length=40
            )
            list_field = serializers.ListField(
                child=serializers.ListField(
                    child=serializers.IntegerField()
                )
            )
            nested_field = NestedField()

        class ExampleView(views.APIView):
            """Example view."""
            def post(self, request):
                pass

            def get_serializer(self):
                return ExampleSerializer()

        view = ExampleView.as_view()
        response = view(request=request)
        expected = {
            'name': 'Example',
            'description': 'Example view.',
            'renders': [
                'application/json',
                'text/html'
            ],
            'parses': [
                'application/json',
                'application/x-www-form-urlencoded',
                'multipart/form-data'
            ],
            'actions': {
                'POST': {
                    'choice_field': {
                        'type': 'choice',
                        'required': True,
                        'read_only': False,
                        'label': 'Choice field',
                        'choices': [
                            {'display_name': 'red', 'value': 'red'},
                            {'display_name': 'green', 'value': 'green'},
                            {'display_name': 'blue', 'value': 'blue'}
                        ]
                    },
                    'integer_field': {
                        'type': 'integer',
                        'required': True,
                        'read_only': False,
                        'label': 'Integer field',
                        'min_value': 1,
                        'max_value': 1000,

                    },
                    'char_field': {
                        'type': 'string',
                        'required': False,
                        'read_only': False,
                        'label': 'Char field',
                        'min_length': 3,
                        'max_length': 40
                    },
                    'list_field': {
                        'type': 'list',
                        'required': True,
                        'read_only': False,
                        'label': 'List field',
                        'child': {
                            'type': 'list',
                            'required': True,
                            'read_only': False,
                            'child': {
                                'type': 'integer',
                                'required': True,
                                'read_only': False
                            }
                        }
                    },
                    'nested_field': {
                        'type': 'nested object',
                        'required': True,
                        'read_only': False,
                        'label': 'Nested field',
                        'children': {
                            'a': {
                                'type': 'integer',
                                'required': True,
                                'read_only': False,
                                'label': 'A'
                            },
                            'b': {
                                'type': 'integer',
                                'required': True,
                                'read_only': False,
                                'label': 'B'
                            }
                        }
                    }
                }
            }
        }
        assert response.status_code == status.HTTP_200_OK
        assert response.data == expected

    def test_global_permissions(self):
        """
        If a user does not have global permissions on an action, then any
        metadata associated with it should not be included in OPTION responses.
        """
        class ExampleSerializer(serializers.Serializer):
            choice_field = serializers.ChoiceField(['red', 'green', 'blue'])
            integer_field = serializers.IntegerField(max_value=10)
            char_field = serializers.CharField(required=False)

        class ExampleView(views.APIView):
            """Example view."""
            def post(self, request):
                pass

            def put(self, request):
                pass

            def get_serializer(self):
                return ExampleSerializer()

            def check_permissions(self, request):
                if request.method == 'POST':
                    raise exceptions.PermissionDenied()

        view = ExampleView.as_view()
        response = view(request=request)
        assert response.status_code == status.HTTP_200_OK
        assert list(response.data['actions'].keys()) == ['PUT']

    def test_object_permissions(self):
        """
        If a user does not have object permissions on an action, then any
        metadata associated with it should not be included in OPTION responses.
        """
        class ExampleSerializer(serializers.Serializer):
            choice_field = serializers.ChoiceField(['red', 'green', 'blue'])
            integer_field = serializers.IntegerField(max_value=10)
            char_field = serializers.CharField(required=False)

        class ExampleView(views.APIView):
            """Example view."""
            def post(self, request):
                pass

            def put(self, request):
                pass

            def get_serializer(self):
                return ExampleSerializer()

            def get_object(self):
                if self.request.method == 'PUT':
                    raise exceptions.PermissionDenied()

        view = ExampleView.as_view()
        response = view(request=request)
        assert response.status_code == status.HTTP_200_OK
        assert list(response.data['actions'].keys()) == ['POST']

    def test_bug_2455_clone_request(self):
        class ExampleView(views.APIView):
            renderer_classes = (BrowsableAPIRenderer,)

            def post(self, request):
                pass

            def get_serializer(self):
                assert hasattr(self.request, 'version')
                return serializers.Serializer()

        view = ExampleView.as_view()
        view(request=request)

    def test_bug_2477_clone_request(self):
        class ExampleView(views.APIView):
            renderer_classes = (BrowsableAPIRenderer,)

            def post(self, request):
                pass

            def get_serializer(self):
                assert hasattr(self.request, 'versioning_scheme')
                return serializers.Serializer()

        scheme = versioning.QueryParameterVersioning
        view = ExampleView.as_view(versioning_class=scheme)
        view(request=request)


class TestFieldMetadata(TestCase):
    simple_metadata = metadata.SimpleMetadata()

    def get_field_metadata(self, field):
        return self.simple_metadata.get_field_info(field)

    def get_serializer_metadata(self, serializer):
        return self.simple_metadata.get_serializer_info(serializer)

    def assertMetadataEqual(self, field, expected_metadata):
        if isinstance(field, serializers.BaseSerializer):
            metadata = self.get_serializer_metadata(field)
        else:
            metadata = self.get_field_metadata(field)
        self.assertEqual(metadata, expected_metadata)

    def test_field(self, field_factory=serializers.Field, expected_type='field', **expected_metadata):
        field = field_factory()
        self.assertMetadataEqual(field, dict({
            'type': expected_type,
            'required': True,
            'read_only': False,
        }, **expected_metadata))
        field = field_factory(
            required=False,
            label=_('label'),
            help_text=_('help text'),
        )
        self.assertMetadataEqual(field, dict({
            'type': expected_type,
            'required': False,
            'read_only': False,
            'label': ugettext('label'),
            'help_text': ugettext('help text'),
        }, **expected_metadata))
        # Empty string label and help_text should be ignored.
        field = field_factory(
            label='',
            help_text='',
        )
        self.assertMetadataEqual(field, dict({
            'type': expected_type,
            'required': True,
            'read_only': False,
        }, **expected_metadata))

    def test_read_only_field(self, field_factory=serializers.ReadOnlyField, expected_type='field',
                             **expected_metadata):
        field = field_factory(read_only=True)
        self.assertMetadataEqual(field, dict({
            'type': expected_type,
            'required': False,
            'read_only': True,
        }, **expected_metadata))

    def test_boolean_field(self):
        self.test_field(serializers.BooleanField, 'boolean')
        self.test_read_only_field(serializers.BooleanField, 'boolean')

    def test_null_boolean_field(self):
        self.test_field(serializers.NullBooleanField, 'boolean')
        self.test_read_only_field(serializers.NullBooleanField, 'boolean')

    def test_char_field(self, field_factory=serializers.CharField, expected_type='string'):
        self.test_field(field_factory, expected_type)
        self.test_read_only_field(field_factory, expected_type)
        field = field_factory(min_length=0, max_length=0)
        self.assertMetadataEqual(field, {
            'type': expected_type,
            'required': True,
            'read_only': False,
            'min_length': 0,
            'max_length': 0,
        })

    def test_email_field(self):
        self.test_char_field(serializers.EmailField, 'email')

    def test_url_field(self):
        self.test_char_field(serializers.URLField, 'url')

    def test_slug_field(self):
        self.test_char_field(serializers.SlugField, 'slug')

    def test_regex_field(self):
        self.test_char_field(functools.partial(serializers.RegexField, regex='regex'), 'regex')

    def test_ip_address_field(self):
        self.test_char_field(serializers.IPAddressField)

    def test_uuid_field(self):
        self.test_field(serializers.UUIDField)
        self.test_read_only_field(serializers.UUIDField)

    def test_integer_field(self, field_factory=serializers.IntegerField, expected_type='integer'):
        self.test_field(field_factory, expected_type)
        self.test_read_only_field(field_factory, expected_type)
        field = field_factory(min_value=0, max_value=0)
        self.assertMetadataEqual(field, {
            'type': expected_type,
            'required': True,
            'read_only': False,
            'min_value': 0,
            'max_value': 0,
        })

    def test_float_field(self):
        self.test_integer_field(serializers.FloatField, 'float')

    def test_decimal_field(self):
        decimal_field_factory = functools.partial(serializers.DecimalField, max_digits=5, decimal_places=2)
        self.test_integer_field(decimal_field_factory, 'decimal')

    def test_date_time_field(self):
        self.test_field(serializers.DateTimeField, 'datetime')
        self.test_read_only_field(serializers.DateTimeField, 'datetime')

    def test_date_field(self):
        self.test_field(serializers.DateField, 'date')
        self.test_read_only_field(serializers.DateField, 'date')

    def test_time_field(self):
        self.test_field(serializers.TimeField, 'time')
        self.test_read_only_field(serializers.TimeField, 'time')

    def test_duration_field(self):
        self.test_field(serializers.DurationField)
        self.test_read_only_field(serializers.DurationField)

    def test_choice_field(self, field_factory=serializers.ChoiceField, expected_type='choice'):
        choice_field_factory = functools.partial(field_factory, choices=[])
        self.test_field(choice_field_factory, expected_type, choices=[])
        self.test_read_only_field(choice_field_factory, expected_type)
        field = field_factory([('value', _('label'))])
        self.assertMetadataEqual(field, {
            'type': expected_type,
            'required': True,
            'read_only': False,
            'choices': [{'value': 'value', 'display_name': ugettext('label')}]
        })

    def test_multiple_choice_field(self):
        self.test_choice_field(serializers.MultipleChoiceField, 'multiple choice')

    def test_file_path_field(self):
        # We have to special case FilePathField as it deals differently with
        # the `required` argument by changing the choices values to include
        # an empty string choice instead.
        path = os.path.dirname(__file__)
        choices = [
            {'value': value, 'display_name': display_name}
            for value, display_name in forms.FilePathField(path, required=False).choices
        ]
        file_path_field_factory = functools.partial(serializers.FilePathField, path=path)
        field = file_path_field_factory()
        self.assertMetadataEqual(field, {
            'type': 'choice',
            'required': True,
            'read_only': False,
            'choices': choices,
        })
        field = file_path_field_factory(
            required=False,
            label=_('label'),
            help_text=_('help text'),
        )
        self.assertMetadataEqual(field, {
            'type': 'choice',
            'required': True,
            'read_only': False,
            'label': ugettext('label'),
            'help_text': ugettext('help text'),
            'choices': choices,
        })
        # Empty string label and help_text should be ignored.
        field = file_path_field_factory(
            label='',
            help_text='',
        )
        self.assertMetadataEqual(field, {
            'type': 'choice',
            'required': True,
            'read_only': False,
            'choices': choices,
        })
        self.test_read_only_field(file_path_field_factory, 'choice')

    def test_file_field(self, field_factory=serializers.FileField, expected_type='file upload'):
        self.test_field(field_factory, expected_type)
        self.test_read_only_field(field_factory, expected_type)
        field = field_factory(max_length=0)
        self.assertMetadataEqual(field, {
            'type': expected_type,
            'required': True,
            'read_only': False,
            'max_length': 0,
        })

    def test_image_field(self):
        self.test_file_field(serializers.ImageField, expected_type='image upload')

    def test_list_field(self):
        def list_field_factory(*args, **kwargs):
            return serializers.ListField(child=serializers.Field(), *args, **kwargs)
        child_metadata = self.get_field_metadata(serializers.Field())
        self.test_field(list_field_factory, 'list', child=child_metadata)
        self.test_read_only_field(list_field_factory, 'list', child=child_metadata)

    def test_dict_field(self):
        def dict_field_factory(*args, **kwargs):
            return serializers.DictField(child=serializers.Field(), *args, **kwargs)
        child_metadata = self.get_field_metadata(serializers.Field())
        self.test_field(dict_field_factory, 'nested object', child=child_metadata)
        self.test_read_only_field(dict_field_factory, 'nested object', child=child_metadata)

    def test_json_field(self):
        self.test_field(serializers.JSONField)
        self.test_read_only_field(serializers.JSONField)

    def test_serializer_method_field(self):
        self.test_read_only_field(functools.partial(serializers.SerializerMethodField, method_name='method'))

    def test_model_field(self):
        model_field_factory = functools.partial(serializers.ModelField, model_field=models.Field())
        self.test_field(model_field_factory)
        self.test_read_only_field(model_field_factory)

    def test_serializer(self):
        class TestSerializer(serializers.Serializer):
            field = serializers.Field()

        serializer = TestSerializer()
        self.assertMetadataEqual(serializer, {
            'field': {
                'type': 'field',
                'required': True,
                'read_only': False,
                'label': 'Field',
            }
        })

        list_serializer = TestSerializer(many=True)
        self.assertMetadataEqual(list_serializer, {
            'field': {
                'type': 'field',
                'required': True,
                'read_only': False,
                'label': 'Field',
            }
        })

    def test_nested_serializer(self):
        class TestNestedSerializer(serializers.Serializer):
            field = serializers.Field()

        class TestSerializer(serializers.Serializer):
            serializer = TestNestedSerializer(
                label=_('label'), help_text=_('help text'), required=True
            )

        serializer = TestSerializer()
        self.assertMetadataEqual(serializer, {
            'serializer': {
                'type': 'nested object',
                'required': True,
                'read_only': False,
                'label': ugettext('label'),
                'help_text': ugettext('help text'),
                'children': {
                    'field': {
                        'type': 'field',
                        'required': True,
                        'read_only': False,
                        'label': 'Field',
                    },
                },
            },
        })

        class TestListSerializer(serializers.Serializer):
            serializer = TestNestedSerializer(many=True)

        list_serializer = TestListSerializer()
        self.assertMetadataEqual(list_serializer, {
            'serializer': {
                'type': 'field',
                'required': True,
                'read_only': False,
                'label': 'Serializer',
                'child': {
                    'type': 'nested object',
                    'required': True,
                    'read_only': False,
                    'children': {
                        'field': {
                            'type': 'field',
                            'required': True,
                            'read_only': False,
                            'label': 'Field',
                        },
                    },
                },
            },
        })


class TestModelSerializerMetadata(TestCase):
    def test_read_only_primary_key_related_field(self):
        """
        On generic views OPTIONS should return an 'actions' key with metadata
        on the fields that may be supplied to PUT and POST requests. It should
        not fail when a read_only PrimaryKeyRelatedField is present
        """
        class Parent(models.Model):
            integer_field = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(1000)])
            children = models.ManyToManyField('Child')
            name = models.CharField(max_length=100, blank=True, null=True)

        class Child(models.Model):
            name = models.CharField(max_length=100)

        class ExampleSerializer(serializers.ModelSerializer):
            children = serializers.PrimaryKeyRelatedField(read_only=True, many=True)

            class Meta:
                model = Parent

        class ExampleView(views.APIView):
            """Example view."""
            def post(self, request):
                pass

            def get_serializer(self):
                return ExampleSerializer()

        view = ExampleView.as_view()
        response = view(request=request)
        expected = {
            'name': 'Example',
            'description': 'Example view.',
            'renders': [
                'application/json',
                'text/html'
            ],
            'parses': [
                'application/json',
                'application/x-www-form-urlencoded',
                'multipart/form-data'
            ],
            'actions': {
                'POST': {
                    'id': {
                        'type': 'integer',
                        'required': False,
                        'read_only': True,
                        'label': 'ID'
                    },
                    'children': {
                        'type': 'field',
                        'required': False,
                        'read_only': True,
                        'label': 'Children'
                    },
                    'integer_field': {
                        'type': 'integer',
                        'required': True,
                        'read_only': False,
                        'label': 'Integer field',
                        'min_value': 1,
                        'max_value': 1000
                    },
                    'name': {
                        'type': 'string',
                        'required': False,
                        'read_only': False,
                        'label': 'Name',
                        'max_length': 100
                    }
                }
            }
        }

        assert response.status_code == status.HTTP_200_OK
        assert response.data == expected
