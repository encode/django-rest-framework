from __future__ import unicode_literals

import urlparse

from django.core.exceptions import ValidationError
from django.core.urlresolvers import get_script_prefix, resolve
from django.utils.translation import ugettext_lazy as _
from django import forms

from rest_framework import serializers
from rest_framework.settings import api_settings


class GenericRelationOption(object):
    """
    This object is responsible for setting up the components needed for providing a generic relation with a given model.
    """

    #TODO: Far more strict evaluation of custom related_field and serializer objects

    # Trying to be inline with common practices
    model_serializer_class = api_settings.DEFAULT_MODEL_SERIALIZER_CLASS

    def __init__(self, model, view_name, as_hyperlink=True, related_field=None, serializer=None):
        self.model = model
        self.view_name = view_name
        self.as_hyperlink = as_hyperlink
        self.related_field = related_field or self.get_default_related_field()
        self.serializer = serializer or self.get_default_serializer()

    def get_output_resolver(self):
        """
        Should return a class that implements the `to_native` method, i.e. `HyperlinkedRelatedField` or `ModelSerializer`.
        """
        if self.as_hyperlink:
            return self.get_prepared_related_field()
        else:
            return self.serializer

    def get_input_resolver(self):
        """
        Should return a class that implements the `from_native` method that can handle URL values,
        i.e. `HyperlinkedRelatedField`.
        """
        return self.get_prepared_related_field()

    def get_prepared_related_field(self):
        """
        Provides the related field with a queryset if not present, based on `self.model`.
        """
        if self.related_field.queryset is None:
            self.related_field.queryset = self.model.objects.all()
        return self.related_field

    def get_default_related_field(self):
        """
        Creates and returns a minimalist ``HyperlinkedRelatedField` instance if none has been passed to the constructor.
        """
        return serializers.HyperlinkedRelatedField(view_name=self.view_name)

    def get_default_serializer(self):
        """
        Creates and returns a minimalist ``ModelSerializer` instance if none has been passed to the constructor.
        """
        class DefaultSerializer(self.model_serializer_class):
            class Meta:
                model = self.model
        return DefaultSerializer()


class GenericRelatedField(serializers.WritableField):
    """
    Represents a generic relation foreign key.

    It's actually more of a wrapper, that delegates the logic to registered fields / serializers based on some
    contenttype framework criteria.
    """
    default_error_messages = {
        'no_model_match': _('Invalid model - model not available.'),
        'no_match': _('Invalid hyperlink - No URL match'),
        'incorrect_match': _('Invalid hyperlink - view name not available'),
    }

    form_field_class = forms.URLField

    def __init__(self, options, *args, **kwargs):
        """
        Needs an extra parameter ``options`` which has to be a list of `GenericRelationOption` objects.
        """
        super(GenericRelatedField, self).__init__(*args, **kwargs)

        # Map for option identifying based on a `Model` class (deserialization cycle)
        self._model_map = dict()
        # Map for option identifying based on a `view_name` (serialization cycle)
        self._view_name_map = dict()

        # Adding the options to the maps.
        for option in options:
            self._model_map[option.model] = option
            self._view_name_map[option.view_name] = option

    def field_to_native(self, obj, field_name):
        """
        Identifies the option object that is responsible for this `value.__class__` (a model) object and returns
        its output serializer's `to_native` method.
        """
        value = super(GenericRelatedField, self).field_to_native(obj, field_name)

        # Retrieving the model class.
        model = value.__class__

        try:
            option = self._model_map[model]
        except KeyError:
            raise ValidationError(self.error_messages['no_model_match'])

        # Get the serializer responsible for output formatting
        serializer = option.get_output_resolver()

        # Necessary because of context, field resolving etc.
        serializer.initialize(self.parent, field_name)

        return serializer.to_native(value)

    def to_native(self, value):
        # Override to prevent the simplifying process of value as present in `WritableField.to_native`.
        return value

    def from_native(self, value):

        # This excerpt is an exact copy of ``rest_framework.relations.HyperlinkedRelatedField``, Line 363
        # From here until ...
        try:
           http_prefix = value.startswith('http:') or value.startswith('https:')
        except AttributeError:
           msg = self.error_messages['incorrect_type']
           raise ValidationError(msg % type(value).__name__)

        if http_prefix:
            # If needed convert absolute URLs to relative path
            value = urlparse.urlparse(value).path
            prefix = get_script_prefix()
            if value.startswith(prefix):
                value = '/' + value[len(prefix):]
        try:
            match = resolve(value)
        except Exception:
            raise ValidationError(self.error_messages['no_match'])

        # ... here. Thinking about putting that in ``rest_framework.utils.py``. Of course With more appropriate exceptions.

        # Try to find the derived `view_name` in the map.
        try:
            view_name = match.url_name
            option = self._view_name_map[view_name]
        except KeyError:
            raise ValidationError(self.error_messages['incorrect_match'])

        # Get the serializer responsible for input resolving
        serializer = option.get_input_resolver()

        # Necessary because of context, field resolving etc.
        serializer.initialize(self.parent, self.source)
        return serializer.from_native(value)
