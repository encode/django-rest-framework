from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django import forms

from rest_framework import six
from rest_framework import serializers
from rest_framework.exceptions import ConfigurationError


class GenericRelatedField(serializers.WritableField):
    """
    Represents a generic relation foreign key.
    It's actually more of a wrapper, that delegates the logic to registered serializers based on the `Model` class.
    """
    default_error_messages = {
        'no_model_match': _('Invalid model - model not available.'),
        'no_url_match': _('Invalid hyperlink - No URL match'),
        'incorrect_url_match': _('Invalid hyperlink - view name not available'),
    }

    form_field_class = forms.URLField

    def __init__(self, serializers, *args, **kwargs):
        """
        Needs an extra parameter `serializers` which has to be a dict key: value being `Model`: serializer.
        """
        super(GenericRelatedField, self).__init__(*args, **kwargs)
        self.serializers = serializers
        for model, serializer in six.iteritems(self.serializers):
            # We have to do it, because the serializer can't access a explicit manager through the
            # GenericForeignKey field on the model.
            if hasattr(serializer, 'queryset') and serializer.queryset is None:
                serializer.queryset = model._default_manager.all()

    def field_to_native(self, obj, field_name):
        """
        Delegates to the `to_native` method of the serializer registered under obj.__class__
        """
        value = super(GenericRelatedField, self).field_to_native(obj, field_name)
        serializer = self.determine_deserializer_for_data(value)

        # Necessary because of context, field resolving etc.
        serializer.initialize(self.parent, field_name)
        return serializer.to_native(value)

    def to_native(self, value):
        # Override to prevent the simplifying process of value as present in `WritableField.to_native`.
        return value

    def from_native(self, value):
        # Get the serializer responsible for input resolving
        try:
            serializer = self.determine_serializer_for_data(value)
        except ConfigurationError as e:
            raise ValidationError(e)
        serializer.initialize(self.parent, self.source)
        return serializer.from_native(value)

    def determine_deserializer_for_data(self, value):
        try:
            model = value.__class__
            serializer = self.serializers[model]
        except KeyError:
            raise ValidationError(self.error_messages['no_model_match'])
        return serializer

    def determine_serializer_for_data(self, value):
        # While one could easily execute the "try" block within from_native and reduce operations, I consider  the
        # concept of serializing is already very naive and vague, that's why I'd go for stringency with the deserialization
        # process here.
        serializers = []
        for serializer in six.itervalues(self.serializers):
            try:
                serializer.from_native(value)
                # Collects all serializers that can handle the input data.
                serializers.append(serializer)
            except:
                pass
        # If no serializer found, raise error.
        l = len(serializers)
        if l < 1:
            raise ConfigurationError('Could not determine a valid serializer for value %r.' % value)
        elif l > 1:
            raise ConfigurationError('There were multiple serializers found for value %r.' % value)
        return serializers[0]
