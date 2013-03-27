"""
# Generic relations

## Introduction

This is an attempt to implement generic relation foreign keys as provided by Django's
[contenttype framework](https://docs.djangoproject.com/en/dev/ref/contrib/contenttypes/) and I tried to follow the
suggestions and requirements described here:
* https://github.com/tomchristie/django-rest-framework/issues/606
* http://stackoverflow.com/a/14454629/1326146

The `GenericRelatedField` field enables you to read and write `GenericForeignKey`s within the scope of Django REST
Framework. While you can decide whether to output `GenericForeignKey`s as nested objects (`ModelSerializer`) or valid
resource URLs (`HyperlinkedRelatedField`), the input is restricted to resource URLs mainly because of two reasons:
* The sheer impossibility of deriving a valid `Model` class from a simple data dictionary.
* My inner storm of indignation when thinking of exposing the actual `ContentType`s to the public scope.

## Disclaimer

Although I'm pretty experienced with Django and REST etc, please note that this piece of code is also my first
experience with Django REST framework at all. I am the maintainer of a pretty large REST service application based on
[tastypie](tastypieapi.org), but Daniel's recent
[blog post](http://toastdriven.com/blog/2013/feb/05/committers-needed-tastypie-haystack/) made me feel a little
uncomfortable. As much I'd like to spend more time contributing, I fear that my current work-life balance doesn't allow
me to do so at the level I'd expect from myself. So I thought it would be a good thing to reach out for other solutions.
It's a good thing anyway, I guess. But a sane and approved way of representing `GenericForeignKeys` is just essential to
the data structure I'm working with. So that's basically why I got in the mix.


## Minimalist example

This is based on the models mentioned in
[this article](http://django-rest-framework.org/api-guide/relations.html#generic-relationships). The examples are also
based on working URL patterns for each model fitting the pattern `<model_lowercase>-detail`.

A minimalist but still working example of a `TagSerializer` with `GenericRelatedField` would look like this:

    class TagSerializer(serializers.ModelSerializer):
        tagged_item = GenericRelatedField([
            GenericRelationOption(Bookmark, 'bookmark-detail'),
            GenericRelationOption(Note, 'note-detail'),
        ], source='tagged_item')

        class Meta:
            model = Tag
            exclude = ('id', 'content_type', 'object_id', )

## ``GenericRelationOption``

Constructor:

    GenericRelationOption(model, view_name, as_hyperlink=True, related_field=None, serializer=None)

**`model`**
The model class.

**`view_name`**
The view name as used in url patterns.

**`as_hyperlink`**
Decides whether the output of the `GenericForeignKey` should be as end point or nested object. In the case of the
latter a generic serializer will be used unless you pass a specific one.

**`related_field`**
A specific subclass of `HyperlinkedRelatedField` that should be used for resolving input data and resolving output data
in case of `as_hyperlink` is `True`.

**`serializer`**
A specific subclass of `ModelSerializer` that should be used for resolving output data
in case of `as_hyperlink` is `True`.

"""
from __future__ import unicode_literals


from django.core.exceptions import ValidationError
from django.core.urlresolvers import get_script_prefix, resolve
from django.utils.translation import ugettext_lazy as _
from django import forms

from rest_framework.compat import  urlparse
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
