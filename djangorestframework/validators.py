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
    bound_form_instance = None

    def validate(self, content):
        """Given some content as input return some cleaned, validated content.
        Raises a ResponseException with status code 400 (Bad Request) on failure.
        
        Validation is standard form validation, with an additional constraint that no extra unknown fields may be supplied.

        On failure the ResponseException content is a dict which may contain 'errors' and 'field-errors' keys.
        If the 'errors' key exists it is a list of strings of non-field errors.
        If the 'field-errors' key exists it is a dict of {field name as string: list of errors as strings}."""
        return self._validate(content)

    def _validate(self, content, allowed_extra_fields=()):
        """Wrapped by validate to hide the extra_fields option that the ModelValidatorMixin uses.
        extra_fields is a list of fields which are not defined by the form, but which we still
        expect to see on the input."""
        bound_form = self.get_bound_form(content)

        if bound_form is None:
            return content
        
        self.bound_form_instance = bound_form

        seen_fields_set = set(content.keys())
        form_fields_set = set(bound_form.fields.keys())
        allowed_extra_fields_set = set(allowed_extra_fields)

        # In addition to regular validation we also ensure no additional fields are being passed in...
        unknown_fields = seen_fields_set - (form_fields_set | allowed_extra_fields_set)

        # Check using both regular validation, and our stricter no additional fields rule
        if bound_form.is_valid() and not unknown_fields:
            # Validation succeeded...
            cleaned_data = bound_form.cleaned_data

            # Add in any extra fields to the cleaned content...
            for key in (allowed_extra_fields_set & seen_fields_set) - set(cleaned_data.keys()):
                cleaned_data[key] = content[key]

            return cleaned_data

        # Validation failed...
        detail = {}

        if not bound_form.errors and not unknown_fields:
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
    raising non-existent field errors, even if they do not exist as fields on the ModelForm.

    Setting the fields class attribute causes the exclude_fields class attribute to be disregarded."""
    fields = None
    
    """The list of fields to exclude from the Model.  This is only used if the fields class attribute is not set."""
    exclude_fields = ('id', 'pk')
    

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
        return self._validate(content, allowed_extra_fields=self._property_fields_set)


    def get_bound_form(self, content=None):
        """Given some content return a Django form bound to that content.

        If the form class attribute has been explicitly set then use that class to create a Form,
        otherwise if model is set use that class to create a ModelForm, otherwise return None."""

        if self.form:
            # Use explict Form
            return super(ModelFormValidatorMixin, self).get_bound_form(content)

        elif self.model:
            # Fall back to ModelForm which we create on the fly
            class OnTheFlyModelForm(forms.ModelForm):
                class Meta:
                    model = self.model
                    #fields = tuple(self._model_fields_set)

            # Instantiate the ModelForm as appropriate
            if content and isinstance(content, models.Model):
                return OnTheFlyModelForm(instance=content)
            elif content:
                return OnTheFlyModelForm(content)
            return OnTheFlyModelForm()

        # Both form and model not set?  Okay bruv, whatevs...
        return None
    

    @property
    def _model_fields_set(self):
        """Return a set containing the names of validated fields on the model."""
        model_fields = set(field.name for field in self.model._meta.fields)

        if self.fields:
            return model_fields & set(as_tuple(self.fields))

        return model_fields - set(as_tuple(self.exclude_fields))
    
    @property
    def _property_fields_set(self):
        """Returns a set containing the names of validated properties on the model."""
        property_fields = set(attr for attr in dir(self.model) if
                              isinstance(getattr(self.model, attr, None), property)
                              and not attr.startswith('_'))

        if self.fields:
            return property_fields & set(as_tuple(self.fields))

        return property_fields - set(as_tuple(self.exclude_fields))
    

    