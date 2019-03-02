from __future__ import unicode_literals

import re

from django.core.validators import MaxValueValidator, RegexValidator
from django.db import models
from django.test import TestCase
from django.utils import six

from rest_framework import generics, serializers, status
from rest_framework.test import APIRequestFactory

factory = APIRequestFactory()


# Regression for #666

class ValidationModel(models.Model):
    blank_validated_field = models.CharField(max_length=255)


class ValidationModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValidationModel
        fields = ('blank_validated_field',)
        read_only_fields = ('blank_validated_field',)


class UpdateValidationModel(generics.RetrieveUpdateDestroyAPIView):
    queryset = ValidationModel.objects.all()
    serializer_class = ValidationModelSerializer


# Regression for #653

class ShouldValidateModel(models.Model):
    should_validate_field = models.CharField(max_length=255)


class ShouldValidateModelSerializer(serializers.ModelSerializer):
    renamed = serializers.CharField(source='should_validate_field', required=False)

    def validate_renamed(self, value):
        if len(value) < 3:
            raise serializers.ValidationError('Minimum 3 characters.')
        return value

    class Meta:
        model = ShouldValidateModel
        fields = ('renamed',)


class TestNestedValidationError(TestCase):
    def test_nested_validation_error_detail(self):
        """
        Ensure nested validation error detail is rendered correctly.
        """
        e = serializers.ValidationError({
            'nested': {
                'field': ['error'],
            }
        })

        assert serializers.as_serializer_error(e) == {
            'nested': {
                'field': ['error'],
            }
        }


class TestPreSaveValidationExclusionsSerializer(TestCase):
    def test_renamed_fields_are_model_validated(self):
        """
        Ensure fields with 'source' applied do get still get model validation.
        """
        # We've set `required=False` on the serializer, but the model
        # does not have `blank=True`, so this serializer should not validate.
        serializer = ShouldValidateModelSerializer(data={'renamed': ''})
        assert serializer.is_valid() is False
        assert 'renamed' in serializer.errors
        assert 'should_validate_field' not in serializer.errors


class TestCustomValidationMethods(TestCase):
    def test_custom_validation_method_is_executed(self):
        serializer = ShouldValidateModelSerializer(data={'renamed': 'fo'})
        assert not serializer.is_valid()
        assert 'renamed' in serializer.errors

    def test_custom_validation_method_passing(self):
        serializer = ShouldValidateModelSerializer(data={'renamed': 'foo'})
        assert serializer.is_valid()


class ValidationSerializer(serializers.Serializer):
    foo = serializers.CharField()

    def validate_foo(self, attrs, source):
        raise serializers.ValidationError("foo invalid")

    def validate(self, attrs):
        raise serializers.ValidationError("serializer invalid")


class TestAvoidValidation(TestCase):
    """
    If serializer was initialized with invalid data (None or non dict-like), it
    should avoid validation layer (validate_<field> and validate methods)
    """
    def test_serializer_errors_has_only_invalid_data_error(self):
        serializer = ValidationSerializer(data='invalid data')
        assert not serializer.is_valid()
        assert serializer.errors == {
            'non_field_errors': [
                'Invalid data. Expected a dictionary, but got %s.' % six.text_type.__name__
            ]
        }


# regression tests for issue: 1493

class ValidationMaxValueValidatorModel(models.Model):
    number_value = models.PositiveIntegerField(validators=[MaxValueValidator(100)])


class ValidationMaxValueValidatorModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValidationMaxValueValidatorModel
        fields = '__all__'


class UpdateMaxValueValidationModel(generics.RetrieveUpdateDestroyAPIView):
    queryset = ValidationMaxValueValidatorModel.objects.all()
    serializer_class = ValidationMaxValueValidatorModelSerializer


class TestMaxValueValidatorValidation(TestCase):

    def test_max_value_validation_serializer_success(self):
        serializer = ValidationMaxValueValidatorModelSerializer(data={'number_value': 99})
        assert serializer.is_valid()

    def test_max_value_validation_serializer_fails(self):
        serializer = ValidationMaxValueValidatorModelSerializer(data={'number_value': 101})
        assert not serializer.is_valid()
        assert serializer.errors == {
            'number_value': [
                'Ensure this value is less than or equal to 100.'
            ]
        }

    def test_max_value_validation_success(self):
        obj = ValidationMaxValueValidatorModel.objects.create(number_value=100)
        request = factory.patch('/{0}'.format(obj.pk), {'number_value': 98}, format='json')
        view = UpdateMaxValueValidationModel().as_view()
        response = view(request, pk=obj.pk).render()
        assert response.status_code == status.HTTP_200_OK

    def test_max_value_validation_fail(self):
        obj = ValidationMaxValueValidatorModel.objects.create(number_value=100)
        request = factory.patch('/{0}'.format(obj.pk), {'number_value': 101}, format='json')
        view = UpdateMaxValueValidationModel().as_view()
        response = view(request, pk=obj.pk).render()
        assert response.content == b'{"number_value":["Ensure this value is less than or equal to 100."]}'
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# regression tests for issue: 1533

class TestChoiceFieldChoicesValidate(TestCase):
    CHOICES = [
        (0, 'Small'),
        (1, 'Medium'),
        (2, 'Large'),
    ]

    SINGLE_CHOICES = [0, 1, 2]

    CHOICES_NESTED = [
        ('Category', (
            (1, 'First'),
            (2, 'Second'),
            (3, 'Third'),
        )),
        (4, 'Fourth'),
    ]

    MIXED_CHOICES = [
        ('Category', (
            (1, 'First'),
            (2, 'Second'),
        )),
        3,
        (4, 'Fourth'),
    ]

    def test_choices(self):
        """
        Make sure a value for choices works as expected.
        """
        f = serializers.ChoiceField(choices=self.CHOICES)
        value = self.CHOICES[0][0]
        try:
            f.to_internal_value(value)
        except serializers.ValidationError:
            self.fail("Value %s does not validate" % str(value))

    def test_single_choices(self):
        """
        Make sure a single value for choices works as expected.
        """
        f = serializers.ChoiceField(choices=self.SINGLE_CHOICES)
        value = self.SINGLE_CHOICES[0]
        try:
            f.to_internal_value(value)
        except serializers.ValidationError:
            self.fail("Value %s does not validate" % str(value))

    def test_nested_choices(self):
        """
        Make sure a nested value for choices works as expected.
        """
        f = serializers.ChoiceField(choices=self.CHOICES_NESTED)
        value = self.CHOICES_NESTED[0][1][0][0]
        try:
            f.to_internal_value(value)
        except serializers.ValidationError:
            self.fail("Value %s does not validate" % str(value))

    def test_mixed_choices(self):
        """
        Make sure mixed values for choices works as expected.
        """
        f = serializers.ChoiceField(choices=self.MIXED_CHOICES)
        value = self.MIXED_CHOICES[1]
        try:
            f.to_internal_value(value)
        except serializers.ValidationError:
            self.fail("Value %s does not validate" % str(value))


class RegexSerializer(serializers.Serializer):
    pin = serializers.CharField(
        validators=[RegexValidator(regex=re.compile('^[0-9]{4,6}$'),
                                   message='A PIN is 4-6 digits')])


expected_repr = """
RegexSerializer():
    pin = CharField(validators=[<django.core.validators.RegexValidator object>])
""".strip()


class TestRegexSerializer(TestCase):
    def test_regex_repr(self):
        serializer_repr = repr(RegexSerializer())
        assert serializer_repr == expected_repr
