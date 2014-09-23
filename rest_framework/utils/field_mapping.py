"""
Helper functions for mapping model fields to a dictionary of default
keyword arguments that should be used for their equivelent serializer fields.
"""
from django.core import validators
from django.db import models
from django.utils.text import capfirst
from rest_framework.compat import clean_manytomany_helptext
import inspect


def lookup_class(mapping, instance):
    """
    Takes a dictionary with classes as keys, and an object.
    Traverses the object's inheritance hierarchy in method
    resolution order, and returns the first matching value
    from the dictionary or raises a KeyError if nothing matches.
    """
    for cls in inspect.getmro(instance.__class__):
        if cls in mapping:
            return mapping[cls]
    raise KeyError('Class %s not found in lookup.', cls.__name__)


def needs_label(model_field, field_name):
    """
    Returns `True` if the label based on the model's verbose name
    is not equal to the default label it would have based on it's field name.
    """
    default_label = field_name.replace('_', ' ').capitalize()
    return capfirst(model_field.verbose_name) != default_label


def get_detail_view_name(model):
    """
    Given a model class, return the view name to use for URL relationships
    that refer to instances of the model.
    """
    return '%(model_name)s-detail' % {
        'app_label': model._meta.app_label,
        'model_name': model._meta.object_name.lower()
    }


def get_field_kwargs(field_name, model_field):
    """
    Creates a default instance of a basic non-relational field.
    """
    kwargs = {}
    validator_kwarg = model_field.validators

    if model_field.null or model_field.blank:
        kwargs['required'] = False

    if model_field.verbose_name and needs_label(model_field, field_name):
        kwargs['label'] = capfirst(model_field.verbose_name)

    if model_field.help_text:
        kwargs['help_text'] = model_field.help_text

    if isinstance(model_field, models.AutoField) or not model_field.editable:
        kwargs['read_only'] = True
        # Read only implies that the field is not required.
        # We have a cleaner repr on the instance if we don't set it.
        kwargs.pop('required', None)

    if model_field.has_default():
        kwargs['default'] = model_field.get_default()
        # Having a default implies that the field is not required.
        # We have a cleaner repr on the instance if we don't set it.
        kwargs.pop('required', None)

    if model_field.flatchoices:
        # If this model field contains choices, then return now,
        # any further keyword arguments are not valid.
        kwargs['choices'] = model_field.flatchoices
        return kwargs

    # Ensure that max_length is passed explicitly as a keyword arg,
    # rather than as a validator.
    max_length = getattr(model_field, 'max_length', None)
    if max_length is not None:
        kwargs['max_length'] = max_length
        validator_kwarg = [
            validator for validator in validator_kwarg
            if not isinstance(validator, validators.MaxLengthValidator)
        ]

    # Ensure that min_length is passed explicitly as a keyword arg,
    # rather than as a validator.
    min_length = getattr(model_field, 'min_length', None)
    if min_length is not None:
        kwargs['min_length'] = min_length
        validator_kwarg = [
            validator for validator in validator_kwarg
            if not isinstance(validator, validators.MinLengthValidator)
        ]

    # Ensure that max_value is passed explicitly as a keyword arg,
    # rather than as a validator.
    max_value = next((
        validator.limit_value for validator in validator_kwarg
        if isinstance(validator, validators.MaxValueValidator)
    ), None)
    if max_value is not None:
        kwargs['max_value'] = max_value
        validator_kwarg = [
            validator for validator in validator_kwarg
            if not isinstance(validator, validators.MaxValueValidator)
        ]

    # Ensure that max_value is passed explicitly as a keyword arg,
    # rather than as a validator.
    min_value = next((
        validator.limit_value for validator in validator_kwarg
        if isinstance(validator, validators.MinValueValidator)
    ), None)
    if min_value is not None:
        kwargs['min_value'] = min_value
        validator_kwarg = [
            validator for validator in validator_kwarg
            if not isinstance(validator, validators.MinValueValidator)
        ]

    # URLField does not need to include the URLValidator argument,
    # as it is explicitly added in.
    if isinstance(model_field, models.URLField):
        validator_kwarg = [
            validator for validator in validator_kwarg
            if not isinstance(validator, validators.URLValidator)
        ]

    # EmailField does not need to include the validate_email argument,
    # as it is explicitly added in.
    if isinstance(model_field, models.EmailField):
        validator_kwarg = [
            validator for validator in validator_kwarg
            if validator is not validators.validate_email
        ]

    # SlugField do not need to include the 'validate_slug' argument,
    if isinstance(model_field, models.SlugField):
        validator_kwarg = [
            validator for validator in validator_kwarg
            if validator is not validators.validate_slug
        ]

    max_digits = getattr(model_field, 'max_digits', None)
    if max_digits is not None:
        kwargs['max_digits'] = max_digits

    decimal_places = getattr(model_field, 'decimal_places', None)
    if decimal_places is not None:
        kwargs['decimal_places'] = decimal_places

    if isinstance(model_field, models.BooleanField):
        # models.BooleanField has `blank=True`, but *is* actually
        # required *unless* a default is provided.
        # Also note that Django<1.6 uses `default=False` for
        # models.BooleanField, but Django>=1.6 uses `default=None`.
        kwargs.pop('required', None)

    if validator_kwarg:
        kwargs['validators'] = validator_kwarg

    # The following will only be used by ModelField classes.
    # Gets removed for everything else.
    kwargs['model_field'] = model_field

    return kwargs


def get_relation_kwargs(field_name, relation_info):
    """
    Creates a default instance of a flat relational field.
    """
    model_field, related_model, to_many, has_through_model = relation_info
    kwargs = {
        'queryset': related_model._default_manager,
        'view_name': get_detail_view_name(related_model)
    }

    if to_many:
        kwargs['many'] = True

    if has_through_model:
        kwargs['read_only'] = True
        kwargs.pop('queryset', None)

    if model_field:
        if model_field.null or model_field.blank:
            kwargs['required'] = False
        if model_field.verbose_name and needs_label(model_field, field_name):
            kwargs['label'] = capfirst(model_field.verbose_name)
        if not model_field.editable:
            kwargs['read_only'] = True
            kwargs.pop('queryset', None)
        help_text = clean_manytomany_helptext(model_field.help_text)
        if help_text:
            kwargs['help_text'] = help_text

    return kwargs


def get_nested_relation_kwargs(relation_info):
    kwargs = {'read_only': True}
    if relation_info.to_many:
        kwargs['many'] = True
    return kwargs


def get_url_kwargs(model_field):
    return {
        'view_name': get_detail_view_name(model_field)
    }
