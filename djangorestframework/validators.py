"""Mixin classes that provide a validate(content) function to validate and cleanup request content"""
from django import forms
from django.db import models
from djangorestframework.response import ResponseException
from djangorestframework.utils import as_tuple

class ValidatorMixin(object):
    """Base class for all ValidatorMixin classes, which simply defines the interface they provide."""

    def validate(self, content):
        """Given some content as input return some cleaned, validated content.
        Raises a ResponseException with status code 400 (Bad Request) on failure.
        
        Must be overridden to be implemented."""
        raise NotImplementedError()


class FormValidatorMixin(ValidatorMixin):
    """Validator Mixin that uses forms for validation.
    Extends the ValidatorMixin interface to also provide a get_bound_form() method.
    (Which may be used by some emitters.)"""
    
    """The form class that should be used for validation, or None to turn off form validation."""
    form = None

    def validate(self, content):
        """Given some content as input return some cleaned, validated content.
        Raises a ResponseException with status code 400 (Bad Request) on failure.
        
        Validation is standard form validation, with an additional constraint that no extra unknown fields may be supplied.

        On failure the ResponseException content is a dict which may contain 'errors' and 'field-errors' keys.
        If the 'errors' key exists it is a list of strings of non-field errors.
        If the 'field-errors' key exists it is a dict of {field name as string: list of errors as strings}."""
        return self._validate(content)

    def _validate(self, content, extra_fields=()):
        """Wrapped by validate to hide the extra_fields option that the ModelValidatorMixin uses.
        extra_fields is a list of fields which are not defined by the form, but which we still
        expect to see on the input."""
        if self.form is None:
            return content
        
        bound_form = self.get_bound_form(content)

        # In addition to regular validation we also ensure no additional fields are being passed in...
        unknown_fields = set(content.keys()) - set(self.form().fields.keys()) - set(extra_fields)

        # And that any extra fields we have specified are all present.
        missing_extra_fields = set(extra_fields) - set(content.keys())

        # Check using both regular validation, and our stricter no additional fields rule
        if bound_form.is_valid() and not unknown_fields and not missing_extra_fields:
            return bound_form.cleaned_data

        # Validation failed...
        detail = {}

        if not bound_form.errors and not unknown_fields and not missing_extra_fields:
            detail = {u'errors': [u'No content was supplied.']}

        else:       
            # Add any non-field errors
            if bound_form.non_field_errors():
                detail[u'errors'] = bound_form.non_field_errors()

            # Add standard field errors
            field_errors = dict((key, map(unicode, val)) for (key, val) in bound_form.errors.iteritems() if not key.startswith('__'))

            # Add any unknown field errors
            for key in unknown_fields:
                field_errors[key] = [u'This field does not exist.']
            
            # Add any missing fields that we required by the extra fields argument
            for key in missing_extra_fields:
                field_errors[key] = [u'This field is required.']
       
            if field_errors:
                detail[u'field-errors'] = field_errors

        # Return HTTP 400 response (BAD REQUEST)
        raise ResponseException(400, detail)
  

    def get_bound_form(self, content=None):
        """Given some content return a Django form bound to that content.
        If form validation is turned off (form class attribute is None) then returns None."""
        if not self.form:
            return None

        if content:
            return self.form(content)
        return self.form()


class ModelFormValidatorMixin(FormValidatorMixin):
    """Validator Mixin that uses forms for validation and falls back to a model form if no form is set.
    Extends the ValidatorMixin interface to also provide a get_bound_form() method.
    (Which may be used by some emitters.)"""
 
    """The form class that should be used for validation, or None to use model form validation."""   
    form = None
    
    """The model class from which the model form should be constructed if no form is set."""
    model = None
    
    """The list of fields we expect to receive as input.  Fields in this list will may be received with
    raising non-existent field errors, even if they do not exist as fields on the ModelForm."""
    fields = None

    # TODO: test the different validation here to allow for get get_absolute_url to be supplied on input and not bork out
    # TODO: be really strict on fields - check they match in the handler methods. (this isn't a validator thing tho.)
    def validate(self, content):
        """Given some content as input return some cleaned, validated content.
        Raises a ResponseException with status code 400 (Bad Request) on failure.
        
        Validation is standard form or model form validation,
        with an additional constraint that no extra unknown fields may be supplied,
        and that all fields specified by the fields class attribute must be supplied,
        even if they are not validated by the form/model form.

        On failure the ResponseException content is a dict which may contain 'errors' and 'field-errors' keys.
        If the 'errors' key exists it is a list of strings of non-field errors.
        If the 'field-errors' key exists it is a dict of {field name as string: list of errors as strings}."""
        extra_fields = set(as_tuple(self.fields)) - set(self.get_bound_form().fields)
        return self._validate(content, extra_fields)


    def get_bound_form(self, content=None):
        """Given some content return a Django form bound to that content.

        If the form class attribute has been explicitly set then use that class to create a Form,
        otherwise if model is set use that class to create a ModelForm, otherwise return None."""
        if self.form:
            # Use explict Form
            return super(ModelFormValidatorMixin, self).get_bound_form(content)

        elif self.model:
            # Fall back to ModelForm which we create on the fly
            class ModelForm(forms.ModelForm):
                class Meta:
                    model = self.model
                    fields = tuple(set.intersection(self.model._meta.fields, self.fields))
                    
            # Instantiate the ModelForm as appropriate
            if content and isinstance(content, models.Model):
                return ModelForm(instance=content)
            elif content:
                return ModelForm(content)
            return ModelForm()

        # Both form and model not set?  Okay bruv, whatevs...
        return None