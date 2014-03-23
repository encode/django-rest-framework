from django.db import models
from django.test import TestCase
from django.core.urlresolvers import reverse

from rest_framework import serializers
from rest_framework import generics
from rest_framework import status
from rest_framework.compat import patterns
from rest_framework.compat import url


class ValidationOnlyFieldsExampleModel(models.Model):
    email = models.EmailField(max_length=100)
    password = models.CharField(max_length=100)


class ValidationOnlyFieldsExampleSerializer(serializers.ModelSerializer):
    password_confirmation = serializers.CharField()
    accept_our_terms_and_conditions = serializers.BooleanField()

    custom_messages = {
        'password_mismatch': 'Password confirmation failed.',
        'terms_condition': 'You must accept our terms and conditions.',
    }

    def validate_password_confirmation(self, attrs, source):
        password_confirmation = attrs[source]
        password = attrs['password']
        if password_confirmation != password:
            raise serializers.ValidationError(self.custom_messages['password_mismatch'])
        return attrs

    def validate_accept_our_terms_and_conditions(self, attrs, source):
        accept_our_terms_and_conditions = attrs[source]
        if not accept_our_terms_and_conditions:
            raise serializers.ValidationError(self.custom_messages['terms_condition'])
        return attrs

    class Meta:
        model = ValidationOnlyFieldsExampleModel
        fields = ('email', 'password', 'password_confirmation', 'accept_our_terms_and_conditions',)
        write_only_fields = ('password',)
        validation_only_fields = ('password_confirmation', 'accept_our_terms_and_conditions',)

    def restore_object(self, attrs, instance=None):
        # Flow: south-bound -- object creation: model instance
        for attr in self.Meta.validation_only_fields:
            attrs.pop(attr)
        return super(ValidationOnlyFieldsExampleSerializer, self).restore_object(attrs, instance)

    def to_native(self, obj):
        try:
            # Flow: north-bound -- form creation: browser API
            return super(ValidationOnlyFieldsExampleSerializer, self).to_native(obj)
        except AttributeError as e:
            # Flow: south-bound -- object validation: model class
            for field in self.Meta.validation_only_fields:
                self.fields.pop(field)
        return super(ValidationOnlyFieldsExampleSerializer, self).to_native(obj)


class ValidationOnlyFieldsExampleView(generics.ListCreateAPIView):
    """
    ValidationOnlyFieldsExampleView
    """
    model = ValidationOnlyFieldsExampleModel
    serializer_class = ValidationOnlyFieldsExampleSerializer

validation_only_fields_test_view = ValidationOnlyFieldsExampleView.as_view()


urlpatterns = patterns('',
    url(
        r'^validation/only/fields/test$',
        validation_only_fields_test_view,
        name='validation_only_fields_test'
    ),
)


class ValidationOnlyFieldsTests(TestCase):
    urls = 'rest_framework.tests.test_validation_only_fields'

    def test_validation_fields_only_not_included_in_data(self):
        data = {
            'email': 'foo@example.com',
            'password': '1234',
            'password_confirmation': '1234',
            'accept_our_terms_and_conditions': True,
        }
        serializer = ValidationOnlyFieldsExampleSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertTrue(isinstance(serializer.object, ValidationOnlyFieldsExampleModel))
        self.assertEquals(serializer.object.email, data['email'])
        self.assertEquals(serializer.object.password, data['password'])
        self.assertFalse(hasattr(serializer.object, 'password_confirmation'))
        self.assertEquals(serializer.data.get('email'), data['email'])
        self.assertEquals(serializer.data.get('password'), None)
        self.assertEquals(serializer.data.get('password_confirmation'), None)

    def test_validation_only_raises_proper_validation_error(self):
        data = {
            'email': 'foo@example.com',
            'password': '1234',
            'password_confirmation': 'ABCD',  # wrong password
            'accept_our_terms_and_conditions': True,
        }
        serializer = ValidationOnlyFieldsExampleSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertEquals(len(serializer.errors), 1)
        self.assertEquals(serializer.errors['password_confirmation'][0],
            ValidationOnlyFieldsExampleSerializer.custom_messages['password_mismatch'])

        data = {
            'email': 'foo@example.com',
            'password': '1234',
            'password_confirmation': 'ABCD',  # wrong password
            'accept_our_terms_and_conditions': False,
        }
        serializer = ValidationOnlyFieldsExampleSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertEquals(len(serializer.errors), 2)
        self.assertEquals(serializer.errors['password_confirmation'][0],
            ValidationOnlyFieldsExampleSerializer.custom_messages['password_mismatch'])
        self.assertEquals(serializer.errors['accept_our_terms_and_conditions'][0],
            ValidationOnlyFieldsExampleSerializer.custom_messages['terms_condition'])

    def test_validation_only_fields_included_in_browser_api_forms(self):
        url = reverse('validation_only_fields_test')
        resp = self.client.get(url, HTTP_ACCEPT='text/html')
        self.assertContains(resp, 'for="email"')
        self.assertContains(resp, 'for="password"')
        self.assertContains(resp, 'for="password_confirmation"')
        self.assertContains(resp, 'for="accept_our_terms_and_conditions"')

    def test_validation_only_fields_not_included_in_reponse(self):
        url = reverse('validation_only_fields_test')
        data = {
            'email': 'foo@example.com',
            'password': '1234',
            'password_confirmation': '1234',
            'accept_our_terms_and_conditions': True,
        }
        resp = self.client.post(url, data=data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEquals(resp.data.get('email'), data['email'])
        self.assertEquals(resp.data.get('password'), None)
        self.assertEquals(resp.data.get('password_confirmation'), None)
        self.assertEquals(resp.data.get('accept_our_terms_and_conditions'), None)
