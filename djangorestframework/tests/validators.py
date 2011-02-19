from django import forms
from django.db import models
from django.test import TestCase
from djangorestframework.compat import RequestFactory
from djangorestframework.validators import ValidatorMixin, FormValidatorMixin, ModelFormValidatorMixin
from djangorestframework.response import ResponseException


class TestValidatorMixinInterfaces(TestCase):
    """Basic tests to ensure that the ValidatorMixin classes expose the expected interfaces"""

    def test_validator_mixin_interface(self):
        """Ensure the ValidatorMixin base class interface is as expected."""
        self.assertRaises(NotImplementedError, ValidatorMixin().validate, None)

    def test_form_validator_mixin_interface(self):
        """Ensure the FormValidatorMixin interface is as expected."""
        self.assertTrue(issubclass(FormValidatorMixin, ValidatorMixin))
        getattr(FormValidatorMixin, 'form')
        getattr(FormValidatorMixin, 'validate')

    def test_model_form_validator_mixin_interface(self):
        """Ensure the ModelFormValidatorMixin interface is as expected."""
        self.assertTrue(issubclass(ModelFormValidatorMixin, FormValidatorMixin))
        getattr(ModelFormValidatorMixin, 'model')
        getattr(ModelFormValidatorMixin, 'form')
        getattr(ModelFormValidatorMixin, 'fields')
        getattr(ModelFormValidatorMixin, 'exclude_fields')
        getattr(ModelFormValidatorMixin, 'validate')


class TestDisabledValidations(TestCase):
    """Tests on Validator Mixins with validation disabled by setting form to None"""

    def test_disabled_form_validator_returns_content_unchanged(self):
        """If the form attribute is None on FormValidatorMixin then validate(content) should just return the content unmodified."""
        class DisabledFormValidator(FormValidatorMixin):
            form = None

        content = {'qwerty':'uiop'}       
        self.assertEqual(DisabledFormValidator().validate(content), content)

    def test_disabled_form_validator_get_bound_form_returns_none(self):
        """If the form attribute is None on FormValidatorMixin then get_bound_form(content) should just return None."""
        class DisabledFormValidator(FormValidatorMixin):
            form = None

        content = {'qwerty':'uiop'}     
        self.assertEqual(DisabledFormValidator().get_bound_form(content), None)

    def test_disabled_model_form_validator_returns_content_unchanged(self):
        """If the form attribute is None on FormValidatorMixin then validate(content) should just return the content unmodified."""
        class DisabledModelFormValidator(ModelFormValidatorMixin):
            form = None

        content = {'qwerty':'uiop'}       
        self.assertEqual(DisabledModelFormValidator().validate(content), content)

    def test_disabled_model_form_validator_get_bound_form_returns_none(self):
        """If the form attribute is None on FormValidatorMixin then get_bound_form(content) should just return None."""
        class DisabledModelFormValidator(ModelFormValidatorMixin):
            form = None

        content = {'qwerty':'uiop'}     
        self.assertEqual(DisabledModelFormValidator().get_bound_form(content), None)


class TestNonFieldErrors(TestCase):
    """Tests against form validation errors caused by non-field errors.  (eg as might be caused by some custom form validation)"""

    def test_validate_failed_due_to_non_field_error_returns_appropriate_message(self):
        """If validation fails with a non-field error, ensure the response a non-field error"""
        class MockForm(forms.Form):
            field1 = forms.CharField(required=False)
            field2 = forms.CharField(required=False)
            ERROR_TEXT = 'You may not supply both field1 and field2'
        
            def clean(self):
                if 'field1' in self.cleaned_data and 'field2' in self.cleaned_data:
                    raise forms.ValidationError(self.ERROR_TEXT)
                return self.cleaned_data  #pragma: no cover
        
        class MockValidator(FormValidatorMixin):
            form = MockForm
        
        content = {'field1': 'example1', 'field2': 'example2'}
        try:
            MockValidator().validate(content)
        except ResponseException, exc:           
            self.assertEqual(exc.response.raw_content, {'errors': [MockForm.ERROR_TEXT]})
        else:
            self.fail('ResourceException was not raised')  #pragma: no cover


class TestFormValidation(TestCase):
    """Tests which check basic form validation.
    Also includes the same set of tests with a ModelFormValidator for which the form has been explicitly set.
    (ModelFormValidatorMixin should behave as FormValidatorMixin if form is set rather than relying on the default ModelForm)"""
    def setUp(self):       
        class MockForm(forms.Form):
            qwerty = forms.CharField(required=True)

        class MockFormValidator(FormValidatorMixin):
            form = MockForm

        class MockModelFormValidator(ModelFormValidatorMixin):
            form = MockForm
        
        self.MockFormValidator = MockFormValidator
        self.MockModelFormValidator = MockModelFormValidator       


    def validation_returns_content_unchanged_if_already_valid_and_clean(self, validator):
        """If the content is already valid and clean then validate(content) should just return the content unmodified."""
        content = {'qwerty':'uiop'}
        self.assertEqual(validator.validate(content), content)

    def validation_failure_raises_response_exception(self, validator):
        """If form validation fails a ResourceException 400 (Bad Request) should be raised."""
        content = {}       
        self.assertRaises(ResponseException, validator.validate, content)

    def validation_does_not_allow_extra_fields_by_default(self, validator):
        """If some (otherwise valid) content includes fields that are not in the form then validation should fail.
        It might be okay on normal form submission, but for Web APIs we oughta get strict, as it'll help show up
        broken clients more easily (eg submitting content with a misnamed field)"""
        content = {'qwerty': 'uiop', 'extra': 'extra'} 
        self.assertRaises(ResponseException, validator.validate, content)

    def validation_allows_extra_fields_if_explicitly_set(self, validator):
        """If we include an allowed_extra_fields paramater on _validate, then allow fields with those names."""
        content = {'qwerty': 'uiop', 'extra': 'extra'} 
        validator._validate(content, allowed_extra_fields=('extra',))

    def validation_does_not_require_extra_fields_if_explicitly_set(self, validator):
        """If we include an allowed_extra_fields paramater on _validate, then do not fail if we do not have fields with those names."""
        content = {'qwerty': 'uiop'} 
        self.assertEqual(validator._validate(content, allowed_extra_fields=('extra',)), content)

    def validation_failed_due_to_no_content_returns_appropriate_message(self, validator):
        """If validation fails due to no content, ensure the response contains a single non-field error"""
        content = {}    
        try:
            validator.validate(content)
        except ResponseException, exc:
            self.assertEqual(exc.response.raw_content, {'errors': ['No content was supplied.']})
        else:
            self.fail('ResourceException was not raised')  #pragma: no cover

    def validation_failed_due_to_field_error_returns_appropriate_message(self, validator):
        """If validation fails due to a field error, ensure the response contains a single field error"""
        content = {'qwerty': ''}
        try:
            validator.validate(content)
        except ResponseException, exc:           
            self.assertEqual(exc.response.raw_content, {'field-errors': {'qwerty': ['This field is required.']}})
        else:
            self.fail('ResourceException was not raised')  #pragma: no cover

    def validation_failed_due_to_invalid_field_returns_appropriate_message(self, validator):
        """If validation fails due to an invalid field, ensure the response contains a single field error"""
        content = {'qwerty': 'uiop', 'extra': 'extra'}
        try:
            validator.validate(content)
        except ResponseException, exc:           
            self.assertEqual(exc.response.raw_content, {'field-errors': {'extra': ['This field does not exist.']}})
        else:
            self.fail('ResourceException was not raised')  #pragma: no cover
    
    def validation_failed_due_to_multiple_errors_returns_appropriate_message(self, validator):
        """If validation for multiple reasons, ensure the response contains each error"""
        content = {'qwerty': '', 'extra': 'extra'}
        try:
            validator.validate(content)
        except ResponseException, exc:           
            self.assertEqual(exc.response.raw_content, {'field-errors': {'qwerty': ['This field is required.'],
                                                                         'extra': ['This field does not exist.']}})
        else:
            self.fail('ResourceException was not raised')  #pragma: no cover

    # Tests on FormValidtionMixin

    def test_form_validation_returns_content_unchanged_if_already_valid_and_clean(self):
        self.validation_returns_content_unchanged_if_already_valid_and_clean(self.MockFormValidator())

    def test_form_validation_failure_raises_response_exception(self):
        self.validation_failure_raises_response_exception(self.MockFormValidator())

    def test_validation_does_not_allow_extra_fields_by_default(self):
        self.validation_does_not_allow_extra_fields_by_default(self.MockFormValidator())

    def test_validation_allows_extra_fields_if_explicitly_set(self):
        self.validation_allows_extra_fields_if_explicitly_set(self.MockFormValidator())

    def test_validation_does_not_require_extra_fields_if_explicitly_set(self):
        self.validation_does_not_require_extra_fields_if_explicitly_set(self.MockFormValidator())

    def test_validation_failed_due_to_no_content_returns_appropriate_message(self):
        self.validation_failed_due_to_no_content_returns_appropriate_message(self.MockFormValidator())

    def test_validation_failed_due_to_field_error_returns_appropriate_message(self):
        self.validation_failed_due_to_field_error_returns_appropriate_message(self.MockFormValidator())

    def test_validation_failed_due_to_invalid_field_returns_appropriate_message(self):
        self.validation_failed_due_to_invalid_field_returns_appropriate_message(self.MockFormValidator())

    def test_validation_failed_due_to_multiple_errors_returns_appropriate_message(self):
        self.validation_failed_due_to_multiple_errors_returns_appropriate_message(self.MockFormValidator())

    # Same tests on ModelFormValidtionMixin

    def test_modelform_validation_returns_content_unchanged_if_already_valid_and_clean(self):
        self.validation_returns_content_unchanged_if_already_valid_and_clean(self.MockModelFormValidator())

    def test_modelform_validation_failure_raises_response_exception(self):
        self.validation_failure_raises_response_exception(self.MockModelFormValidator())

    def test_modelform_validation_does_not_allow_extra_fields_by_default(self):
        self.validation_does_not_allow_extra_fields_by_default(self.MockModelFormValidator())

    def test_modelform_validation_allows_extra_fields_if_explicitly_set(self):
        self.validation_allows_extra_fields_if_explicitly_set(self.MockModelFormValidator())

    def test_modelform_validation_does_not_require_extra_fields_if_explicitly_set(self):
        self.validation_does_not_require_extra_fields_if_explicitly_set(self.MockModelFormValidator())

    def test_modelform_validation_failed_due_to_no_content_returns_appropriate_message(self):
        self.validation_failed_due_to_no_content_returns_appropriate_message(self.MockModelFormValidator())

    def test_modelform_validation_failed_due_to_field_error_returns_appropriate_message(self):
        self.validation_failed_due_to_field_error_returns_appropriate_message(self.MockModelFormValidator())

    def test_modelform_validation_failed_due_to_invalid_field_returns_appropriate_message(self):
        self.validation_failed_due_to_invalid_field_returns_appropriate_message(self.MockModelFormValidator())

    def test_modelform_validation_failed_due_to_multiple_errors_returns_appropriate_message(self):
        self.validation_failed_due_to_multiple_errors_returns_appropriate_message(self.MockModelFormValidator())


class TestModelFormValidator(TestCase):
    """Tests specific to ModelFormValidatorMixin"""
    
    def setUp(self):
        """Create a validator for a model with two fields and a property."""    
        class MockModel(models.Model):
            qwerty = models.CharField(max_length=256)
            uiop = models.CharField(max_length=256, blank=True)
            
            @property
            def readonly(self):
                return 'read only'
            
        class MockValidator(ModelFormValidatorMixin):
            model = MockModel
       
        self.MockValidator = MockValidator


    def test_property_fields_are_allowed_on_model_forms(self):
        """Validation on ModelForms may include property fields that exist on the Model to be included in the input."""
        content = {'qwerty':'example', 'uiop': 'example', 'readonly': 'read only'}
        self.assertEqual(self.MockValidator().validate(content), content)

    def test_property_fields_are_not_required_on_model_forms(self):
        """Validation on ModelForms does not require property fields that exist on the Model to be included in the input."""
        content = {'qwerty':'example', 'uiop': 'example'}
        self.assertEqual(self.MockValidator().validate(content), content)

    def test_extra_fields_not_allowed_on_model_forms(self):
        """If some (otherwise valid) content includes fields that are not in the form then validation should fail.
        It might be okay on normal form submission, but for Web APIs we oughta get strict, as it'll help show up
        broken clients more easily (eg submitting content with a misnamed field)"""
        content = {'qwerty': 'example', 'uiop':'example', 'readonly': 'read only', 'extra': 'extra'} 
        self.assertRaises(ResponseException, self.MockValidator().validate, content)
    
    def test_validate_requires_fields_on_model_forms(self):
        """If some (otherwise valid) content includes fields that are not in the form then validation should fail.
        It might be okay on normal form submission, but for Web APIs we oughta get strict, as it'll help show up
        broken clients more easily (eg submitting content with a misnamed field)"""
        content = {'readonly': 'read only'} 
        self.assertRaises(ResponseException, self.MockValidator().validate, content)
    
    def test_validate_does_not_require_blankable_fields_on_model_forms(self):
        """Test standard ModelForm validation behaviour - fields with blank=True are not required."""
        content = {'qwerty':'example', 'readonly': 'read only'}
        self.MockValidator().validate(content)
    
    def test_model_form_validator_uses_model_forms(self):
        self.assertTrue(isinstance(self.MockValidator().get_bound_form(), forms.ModelForm))


