from django import forms
from django.test import TestCase
from djangorestframework.tests.utils import RequestFactory
from djangorestframework.validators import ValidatorMixin, FormValidatorMixin, ModelFormValidatorMixin
from djangorestframework.response import ResponseException


class TestValidatorMixins(TestCase):
    def setUp(self):
        self.req = RequestFactory()
        
        class MockForm(forms.Form):
            qwerty = forms.CharField(required=True)

        class MockValidator(FormValidatorMixin):
            form = MockForm

        class DisabledValidator(FormValidatorMixin):
            form = None
        
        self.MockValidator = MockValidator
        self.DisabledValidator = DisabledValidator       

        
    # Interface tests

    def test_validator_mixin_interface(self):
        """Ensure the ContentMixin interface is as expected."""
        self.assertRaises(NotImplementedError, ValidatorMixin().validate, None)

    def test_form_validator_mixin_interface(self):
        """Ensure the OverloadedContentMixin interface is as expected."""
        self.assertTrue(issubclass(FormValidatorMixin, ValidatorMixin))
        getattr(FormValidatorMixin, 'form')
        getattr(FormValidatorMixin, 'validate')

    def test_model_form_validator_mixin_interface(self):
        """Ensure the OverloadedContentMixin interface is as expected."""
        self.assertTrue(issubclass(ModelFormValidatorMixin, FormValidatorMixin))
        getattr(ModelFormValidatorMixin, 'model')
        getattr(ModelFormValidatorMixin, 'form')
        getattr(ModelFormValidatorMixin, 'validate')

    # Behavioural tests - FormValidatorMixin
    
    def test_validate_returns_content_unchanged_if_no_form_is_set(self):
        """If the form attribute is None then validate(content) should just return the content unmodified."""
        content = {'qwerty':'uiop'}       
        self.assertEqual(self.DisabledValidator().validate(content), content)

    def test_get_bound_form_returns_none_if_no_form_is_set(self):
        """If the form attribute is None then get_bound_form(content) should just return None."""
        content = {'qwerty':'uiop'}     
        self.assertEqual(self.DisabledValidator().get_bound_form(content), None)

    def test_validate_returns_content_unchanged_if_validates_and_does_not_need_cleanup(self):
        """If the content is already valid and clean then validate(content) should just return the content unmodified."""
        content = {'qwerty':'uiop'}
       
        self.assertEqual(self.MockValidator().validate(content), content)

    def test_form_validation_failure_raises_response_exception(self):
        """If form validation fails a ResourceException 400 (Bad Request) should be raised."""
        content = {}       
        self.assertRaises(ResponseException, self.MockValidator().validate, content)

    def test_validate_does_not_allow_extra_fields(self):
        """If some (otherwise valid) content includes fields that are not in the form then validation should fail.
        It might be okay on normal form submission, but for Web APIs we oughta get strict, as it'll help show up
        broken clients more easily (eg submitting content with a misnamed field)"""
        content = {'qwerty': 'uiop', 'extra': 'extra'} 
        self.assertRaises(ResponseException, self.MockValidator().validate, content)

    def test_validate_allows_extra_fields_if_explicitly_set(self):
        """If we include an extra_fields paramater on _validate, then allow fields with those names."""
        content = {'qwerty': 'uiop', 'extra': 'extra'} 
        self.MockValidator()._validate(content, extra_fields=('extra',))

    def test_validate_checks_for_extra_fields_if_explicitly_set(self):
        """If we include an extra_fields paramater on _validate, then fail unless we have fields with those names."""
        content = {'qwerty': 'uiop'} 
        try:
            self.MockValidator()._validate(content, extra_fields=('extra',))
        except ResponseException, exc:
            self.assertEqual(exc.response.raw_content, {'field-errors': {'extra': ['This field is required.']}})
        else:
            self.fail('ResourceException was not raised')  #pragma: no cover

    def test_validate_failed_due_to_no_content_returns_appropriate_message(self):
        """If validation fails due to no content, ensure the response contains a single non-field error"""
        content = {}    
        try:
            self.MockValidator().validate(content)
        except ResponseException, exc:
            self.assertEqual(exc.response.raw_content, {'errors': ['No content was supplied.']})
        else:
            self.fail('ResourceException was not raised')  #pragma: no cover

    def test_validate_failed_due_to_field_error_returns_appropriate_message(self):
        """If validation fails due to a field error, ensure the response contains a single field error"""
        content = {'qwerty': ''}
        try:
            self.MockValidator().validate(content)
        except ResponseException, exc:           
            self.assertEqual(exc.response.raw_content, {'field-errors': {'qwerty': ['This field is required.']}})
        else:
            self.fail('ResourceException was not raised')  #pragma: no cover

    def test_validate_failed_due_to_invalid_field_returns_appropriate_message(self):
        """If validation fails due to an invalid field, ensure the response contains a single field error"""
        content = {'qwerty': 'uiop', 'extra': 'extra'}
        try:
            self.MockValidator().validate(content)
        except ResponseException, exc:           
            self.assertEqual(exc.response.raw_content, {'field-errors': {'extra': ['This field does not exist.']}})
        else:
            self.fail('ResourceException was not raised')  #pragma: no cover
    
    def test_validate_failed_due_to_multiple_errors_returns_appropriate_message(self):
        """If validation for multiple reasons, ensure the response contains each error"""
        content = {'qwerty': '', 'extra': 'extra'}
        try:
            self.MockValidator().validate(content)
        except ResponseException, exc:           
            self.assertEqual(exc.response.raw_content, {'field-errors': {'qwerty': ['This field is required.'],
                                                                         'extra': ['This field does not exist.']}})
        else:
            self.fail('ResourceException was not raised')  #pragma: no cover
    
    def test_validate_failed_due_to_non_field_error_returns_appropriate_message(self):
        """If validation for with a non-field error, ensure the response a non-field error"""
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