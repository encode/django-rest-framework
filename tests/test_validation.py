from __future__ import unicode_literals
from django.db import models
from django.test import TestCase
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
    model = ValidationModel
    serializer_class = ValidationModelSerializer


class TestPreSaveValidationExclusions(TestCase):
    def test_pre_save_validation_exclusions(self):
        """
        Somewhat weird test case to ensure that we don't perform model
        validation on read only fields.
        """
        obj = ValidationModel.objects.create(blank_validated_field='')
        request = factory.put('/', {}, format='json')
        view = UpdateValidationModel().as_view()
        response = view(request, pk=obj.pk).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# Regression for #653

class ShouldValidateModel(models.Model):
    should_validate_field = models.CharField(max_length=255)


class ShouldValidateModelSerializer(serializers.ModelSerializer):
    renamed = serializers.CharField(source='should_validate_field', required=False)

    def validate_renamed(self, attrs, source):
        value = attrs[source]
        if len(value) < 3:
            raise serializers.ValidationError('Minimum 3 characters.')
        return attrs

    class Meta:
        model = ShouldValidateModel
        fields = ('renamed',)


class TestPreSaveValidationExclusionsSerializer(TestCase):
    def test_renamed_fields_are_model_validated(self):
        """
        Ensure fields with 'source' applied do get still get model validation.
        """
        # We've set `required=False` on the serializer, but the model
        # does not have `blank=True`, so this serializer should not validate.
        serializer = ShouldValidateModelSerializer(data={'renamed': ''})
        self.assertEqual(serializer.is_valid(), False)
        self.assertIn('renamed', serializer.errors)
        self.assertNotIn('should_validate_field', serializer.errors)


class TestCustomValidationMethods(TestCase):
    def test_custom_validation_method_is_executed(self):
        serializer = ShouldValidateModelSerializer(data={'renamed': 'fo'})
        self.assertFalse(serializer.is_valid())
        self.assertIn('renamed', serializer.errors)

    def test_custom_validation_method_passing(self):
        serializer = ShouldValidateModelSerializer(data={'renamed': 'foo'})
        self.assertTrue(serializer.is_valid())


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
        self.assertFalse(serializer.is_valid())
        self.assertDictEqual(serializer.errors,
                             {'non_field_errors': ['Invalid data']})
