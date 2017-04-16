from django.db import models
from django.test import TestCase

from rest_framework import serializers
from rest_framework import generics
from rest_framework.compat import patterns, url


class CustomFieldExampleModel(models.Model):
    email = models.EmailField(max_length=100)
    password = models.CharField(max_length=100)


# ------ use only restore_object ------ #

class CustomFieldExampleSerializer(serializers.ModelSerializer):
    password_confirmation = serializers.CharField()
    
    def validate_password_confirmation(self, attrs, source):
        password_confirmation = attrs[source]
        password = attrs['password']
        if password_confirmation != password:
            raise serializers.ValidationError('Password confirmation mismatch')
            attrs.pop(source)
        return attrs
    
    def restore_object(self, attrs, instance=None):
        attrs.pop('password_confirmation')
        return super(CustomFieldExampleSerializer, self).restore_object(attrs, instance)
    
    class Meta:
        model = CustomFieldExampleModel
        fields = ('email', 'password', 'password_confirmation',)
        write_only_fields = ('password',)


class CustomFieldExampleView(generics.ListCreateAPIView):
    """
    CustomFieldExampleView
    """
    model = CustomFieldExampleModel
    serializer_class = CustomFieldExampleSerializer

custom_field_view = CustomFieldExampleView.as_view()


# ------ use restore_object and to_native ------ #

class CustomField2ExampleSerializer(CustomFieldExampleSerializer):
    
    def to_native(self, obj):
        self.fields.pop('password_confirmation')
        return super(CustomField2ExampleSerializer, self).to_native(obj)


class CustomField2ExampleView(generics.ListCreateAPIView):
    """
    CustomFieldExampleView
    """
    model = CustomFieldExampleModel
    serializer_class = CustomField2ExampleSerializer

custom_field2_view = CustomField2ExampleView.as_view()


# ------ urls ------ #

urlpatterns = patterns('',
    url(r'^custom_field$', custom_field_view),
    url(r'^custom_field2$', custom_field2_view),
)


class CustomFieldsTests(TestCase):
    urls = 'rest_framework.tests.test_serializer_custom_field'
    
    def test_custom_field(self):
        data = {
            'email': 'foo@example.com',
            'password': '123',
            'password_confirmation': '123',
        }
        serializer = CustomFieldExampleSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertTrue(isinstance(serializer.object, CustomFieldExampleModel))
        self.assertEquals(serializer.object.email, data['email'])
        self.assertEquals(serializer.object.password, data['password'])
        self.assertEquals(serializer.data, {'email': 'foo@example.com'})

    def test_custom_field_validation_error(self):
        data = {
            'email': 'foo@example.com',
            'password': '123',
            'password_confirmation': 'abc',
        }
        serializer = CustomFieldExampleSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertEquals(len(serializer.errors), 1)
        self.assertEquals(serializer.errors['password_confirmation'],
            ['Password confirmation mismatch'])
    
    def test_custom_field_displayed_in_html_version(self):
        """
        Ensure password_confirmation field is shown in the browsable API form
        """
        response = self.client.get('/custom_field', HTTP_ACCEPT='text/html')
        self.assertContains(response, 'for="password"')
        self.assertContains(response, 'for="password_confirmation"')
    
    # --- 2 --- #
    
    def test_custom_field2(self):
        data = {
            'email': 'foo@example.com',
            'password': '123',
            'password_confirmation': '123',
        }
        serializer = CustomField2ExampleSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertTrue(isinstance(serializer.object, CustomFieldExampleModel))
        self.assertEquals(serializer.object.email, data['email'])
        self.assertEquals(serializer.object.password, data['password'])
        self.assertEquals(serializer.data, {'email': 'foo@example.com'})

    def test_custom_field2_validation_error(self):
        data = {
            'email': 'foo@example.com',
            'password': '123',
            'password_confirmation': 'abc',
        }
        serializer = CustomField2ExampleSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertEquals(len(serializer.errors), 1)
        self.assertEquals(serializer.errors['password_confirmation'],
            ['Password confirmation mismatch'])
    
    def test_custom_field2_displayed_in_html_version(self):
        """
        Ensure password_confirmation field is shown in the browsable API form
        """
        response = self.client.get('/custom_field2', HTTP_ACCEPT='text/html')
        self.assertContains(response, 'for="password"')
        self.assertContains(response, 'for="password_confirmation"')