"""
Serializer fields that deal with relationships.

These fields allow you to specify the style that should be used to represent
model relationships, including hyperlinks, primary keys, or slugs.
"""
from __future__ import unicode_literals
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.urlresolvers import resolve, get_script_prefix, NoReverseMatch
from django import forms
from django.db.models.fields import BLANK_CHOICE_DASH
from django.forms import widgets
from django.forms.models import ModelChoiceIterator
from django.utils.translation import ugettext_lazy as _
from rest_framework.fields import Field, WritableField, get_component
from rest_framework.reverse import reverse
from rest_framework.compat import urlparse
from rest_framework.compat import smart_text
import warnings


##### Relational fields #####


# Not actually Writable, but subclasses may need to be.
class RelatedField(WritableField):
    """
    Base class for related model fields.

    This represents a relationship using the unicode representation of the target.
    """
    widget = widgets.Select
    many_widget = widgets.SelectMultiple
    form_field_class = forms.ChoiceField
    many_form_field_class = forms.MultipleChoiceField

    cache_choices = False
    empty_label = None
    read_only = True
    many = False

    def __init__(self, *args, **kwargs):

        # 'null' is to be deprecated in favor of 'required'
        if 'null' in kwargs:
            warnings.warn('The `null` keyword argument is deprecated. '
                          'Use the `required` keyword argument instead.',
                          DeprecationWarning, stacklevel=2)
            kwargs['required'] = not kwargs.pop('null')

        queryset = kwargs.pop('queryset', None)
        self.many = kwargs.pop('many', self.many)
        if self.many:
            self.widget = self.many_widget
            self.form_field_class = self.many_form_field_class

        kwargs['read_only'] = kwargs.pop('read_only', self.read_only)
        super(RelatedField, self).__init__(*args, **kwargs)

        if not self.required:
            self.empty_label = BLANK_CHOICE_DASH[0][1]

        self.queryset = queryset

    def initialize(self, parent, field_name):
        super(RelatedField, self).initialize(parent, field_name)
        if self.queryset is None and not self.read_only:
            try:
                manager = getattr(self.parent.opts.model, self.source or field_name)
                if hasattr(manager, 'related'):  # Forward
                    self.queryset = manager.related.model._default_manager.all()
                else:  # Reverse
                    self.queryset = manager.field.rel.to._default_manager.all()
            except Exception:
                msg = ('Serializer related fields must include a `queryset`' +
                       ' argument or set `read_only=True')
                raise Exception(msg)

    ### We need this stuff to make form choices work...

    def prepare_value(self, obj):
        return self.to_native(obj)

    def label_from_instance(self, obj):
        """
        Return a readable representation for use with eg. select widgets.
        """
        desc = smart_text(obj)
        ident = smart_text(self.to_native(obj))
        if desc == ident:
            return desc
        return "%s - %s" % (desc, ident)

    def _get_queryset(self):
        return self._queryset

    def _set_queryset(self, queryset):
        self._queryset = queryset
        self.widget.choices = self.choices

    queryset = property(_get_queryset, _set_queryset)

    def _get_choices(self):
        # If self._choices is set, then somebody must have manually set
        # the property self.choices. In this case, just return self._choices.
        if hasattr(self, '_choices'):
            return self._choices

        # Otherwise, execute the QuerySet in self.queryset to determine the
        # choices dynamically. Return a fresh ModelChoiceIterator that has not been
        # consumed. Note that we're instantiating a new ModelChoiceIterator *each*
        # time _get_choices() is called (and, thus, each time self.choices is
        # accessed) so that we can ensure the QuerySet has not been consumed. This
        # construct might look complicated but it allows for lazy evaluation of
        # the queryset.
        return ModelChoiceIterator(self)

    def _set_choices(self, value):
        # Setting choices also sets the choices on the widget.
        # choices can be any iterable, but we call list() on it because
        # it will be consumed more than once.
        self._choices = self.widget.choices = list(value)

    choices = property(_get_choices, _set_choices)

    ### Regular serializer stuff...

    def field_to_native(self, obj, field_name):
        try:
            if self.source == '*':
                return self.to_native(obj)

            source = self.source or field_name
            value = obj

            for component in source.split('.'):
                value = get_component(value, component)
                if value is None:
                    break
        except ObjectDoesNotExist:
            return None

        if value is None:
            return None

        if self.many:
            return [self.to_native(item) for item in value.all()]
        return self.to_native(value)

    def field_from_native(self, data, files, field_name, into):
        if self.read_only:
            return

        try:
            if self.many:
                try:
                    # Form data
                    value = data.getlist(field_name)
                    if value == [''] or value == []:
                        raise KeyError
                except AttributeError:
                    # Non-form data
                    value = data[field_name]
            else:
                value = data[field_name]
        except KeyError:
            if self.partial:
                return
            value = [] if self.many else None

        if value in (None, '') and self.required:
            raise ValidationError(self.error_messages['required'])
        elif value in (None, ''):
            into[(self.source or field_name)] = None
        elif self.many:
            into[(self.source or field_name)] = [self.from_native(item) for item in value]
        else:
            into[(self.source or field_name)] = self.from_native(value)


### PrimaryKey relationships

class PrimaryKeyRelatedField(RelatedField):
    """
    Represents a relationship as a pk value.
    """
    read_only = False

    default_error_messages = {
        'does_not_exist': _("Invalid pk '%s' - object does not exist."),
        'incorrect_type': _('Incorrect type.  Expected pk value, received %s.'),
    }

    # TODO: Remove these field hacks...
    def prepare_value(self, obj):
        return self.to_native(obj.pk)

    def label_from_instance(self, obj):
        """
        Return a readable representation for use with eg. select widgets.
        """
        desc = smart_text(obj)
        ident = smart_text(self.to_native(obj.pk))
        if desc == ident:
            return desc
        return "%s - %s" % (desc, ident)

    # TODO: Possibly change this to just take `obj`, through prob less performant
    def to_native(self, pk):
        return pk

    def from_native(self, data):
        if self.queryset is None:
            raise Exception('Writable related fields must include a `queryset` argument')

        try:
            return self.queryset.get(pk=data)
        except ObjectDoesNotExist:
            msg = self.error_messages['does_not_exist'] % smart_text(data)
            raise ValidationError(msg)
        except (TypeError, ValueError):
            received = type(data).__name__
            msg = self.error_messages['incorrect_type'] % received
            raise ValidationError(msg)

    def field_to_native(self, obj, field_name):
        if self.many:
            # To-many relationship

            queryset = None
            if not self.source:
                # Prefer obj.serializable_value for performance reasons
                try:
                    queryset = obj.serializable_value(field_name)
                except AttributeError:
                    pass
            if queryset is None:
                # RelatedManager (reverse relationship)
                source = self.source or field_name
                queryset = obj
                for component in source.split('.'):
                    queryset = get_component(queryset, component)

            # Forward relationship
            return [self.to_native(item.pk) for item in queryset.all()]

        # To-one relationship
        try:
            # Prefer obj.serializable_value for performance reasons
            pk = obj.serializable_value(self.source or field_name)
        except AttributeError:
            # RelatedObject (reverse relationship)
            try:
                pk = getattr(obj, self.source or field_name).pk
            except ObjectDoesNotExist:
                return None

        # Forward relationship
        return self.to_native(pk)


### Slug relationships


class SlugRelatedField(RelatedField):
    """
    Represents a relationship using a unique field on the target.
    """
    read_only = False

    default_error_messages = {
        'does_not_exist': _("Object with %s=%s does not exist."),
        'invalid': _('Invalid value.'),
    }

    def __init__(self, *args, **kwargs):
        self.slug_field = kwargs.pop('slug_field', None)
        assert self.slug_field, 'slug_field is required'
        super(SlugRelatedField, self).__init__(*args, **kwargs)

    def to_native(self, obj):
        return getattr(obj, self.slug_field)

    def from_native(self, data):
        if self.queryset is None:
            raise Exception('Writable related fields must include a `queryset` argument')

        try:
            return self.queryset.get(**{self.slug_field: data})
        except ObjectDoesNotExist:
            raise ValidationError(self.error_messages['does_not_exist'] %
                                  (self.slug_field, smart_text(data)))
        except (TypeError, ValueError):
            msg = self.error_messages['invalid']
            raise ValidationError(msg)


### Hyperlinked relationships

class HyperlinkedRelatedField(RelatedField):
    """
    Represents a relationship using hyperlinking.
    """
    read_only = False
    lookup_field = 'pk'

    default_error_messages = {
        'no_match': _('Invalid hyperlink - No URL match'),
        'incorrect_match': _('Invalid hyperlink - Incorrect URL match'),
        'configuration_error': _('Invalid hyperlink due to configuration error'),
        'does_not_exist': _("Invalid hyperlink - object does not exist."),
        'incorrect_type': _('Incorrect type.  Expected url string, received %s.'),
    }

    # These are all pending deprecation
    pk_url_kwarg = 'pk'
    slug_field = 'slug'
    slug_url_kwarg = None  # Defaults to same as `slug_field` unless overridden

    def __init__(self, *args, **kwargs):
        try:
            self.view_name = kwargs.pop('view_name')
        except KeyError:
            raise ValueError("Hyperlinked field requires 'view_name' kwarg")

        self.lookup_field = kwargs.pop('lookup_field', self.lookup_field)
        self.format = kwargs.pop('format', None)

        # These are pending deprecation
        if 'pk_url_kwarg' in kwargs:
            msg = 'pk_url_kwarg is pending deprecation. Use lookup_field instead.'
            warnings.warn(msg, PendingDeprecationWarning, stacklevel=2)
        if 'slug_url_kwarg' in kwargs:
            msg = 'slug_url_kwarg is pending deprecation. Use lookup_field instead.'
            warnings.warn(msg, PendingDeprecationWarning, stacklevel=2)
        if 'slug_field' in kwargs:
            msg = 'slug_field is pending deprecation. Use lookup_field instead.'
            warnings.warn(msg, PendingDeprecationWarning, stacklevel=2)

        self.pk_url_kwarg = kwargs.pop('pk_url_kwarg', self.pk_url_kwarg)
        self.slug_field = kwargs.pop('slug_field', self.slug_field)
        default_slug_kwarg = self.slug_url_kwarg or self.slug_field
        self.slug_url_kwarg = kwargs.pop('slug_url_kwarg', default_slug_kwarg)

        super(HyperlinkedRelatedField, self).__init__(*args, **kwargs)

    def get_url(self, obj, view_name, request, format):
        """
        Given an object, return the URL that hyperlinks to the object.

        May raise a `NoReverseMatch` if the `view_name` and `lookup_field`
        attributes are not configured to correctly match the URL conf.
        """
        lookup_field = getattr(obj, self.lookup_field)
        kwargs = {self.lookup_field: lookup_field}
        try:
            return reverse(view_name, kwargs=kwargs, request=request, format=format)
        except NoReverseMatch:
            pass

        if self.pk_url_kwarg != 'pk':
            # Only try pk if it has been explicitly set.
            # Otherwise, the default `lookup_field = 'pk'` has us covered.
            pk = obj.pk
            kwargs = {self.pk_url_kwarg: pk}
            try:
                return reverse(view_name, kwargs=kwargs, request=request, format=format)
            except NoReverseMatch:
                pass

        slug = getattr(obj, self.slug_field, None)
        if slug is not None:
            # Only try slug if it corresponds to an attribute on the object.
            kwargs = {self.slug_url_kwarg: slug}
            try:
                ret = reverse(view_name, kwargs=kwargs, request=request, format=format)
                if self.slug_field == 'slug' and self.slug_url_kwarg == 'slug':
                    # If the lookup succeeds using the default slug params,
                    # then `slug_field` is being used implicitly, and we
                    # we need to warn about the pending deprecation.
                    msg = 'Implicit slug field hyperlinked fields are pending deprecation.' \
                          'You should set `lookup_field=slug` on the HyperlinkedRelatedField.'
                    warnings.warn(msg, PendingDeprecationWarning, stacklevel=2)
                return ret
            except NoReverseMatch:
                pass

        raise NoReverseMatch()

    def get_object(self, queryset, view_name, view_args, view_kwargs):
        """
        Return the object corresponding to a matched URL.

        Takes the matched URL conf arguments, and the queryset, and should
        return an object instance, or raise an `ObjectDoesNotExist` exception.
        """
        lookup = view_kwargs.get(self.lookup_field, None)
        pk = view_kwargs.get(self.pk_url_kwarg, None)
        slug = view_kwargs.get(self.slug_url_kwarg, None)

        if lookup is not None:
            filter_kwargs = {self.lookup_field: lookup}
        elif pk is not None:
            filter_kwargs = {'pk': pk}
        elif slug is not None:
            filter_kwargs = {self.slug_field: slug}
        else:
            raise ObjectDoesNotExist()

        return queryset.get(**filter_kwargs)

    def to_native(self, obj):
        view_name = self.view_name
        request = self.context.get('request', None)
        format = self.format or self.context.get('format', None)

        if request is None:
            msg = (
                "Using `HyperlinkedRelatedField` without including the request "
                "in the serializer context is deprecated. "
                "Add `context={'request': request}` when instantiating "
                "the serializer."
            )
            warnings.warn(msg, DeprecationWarning, stacklevel=4)

        # If the object has not yet been saved then we cannot hyperlink to it.
        if getattr(obj, 'pk', None) is None:
            return

        # Return the hyperlink, or error if incorrectly configured.
        try:
            return self.get_url(obj, view_name, request, format)
        except NoReverseMatch:
            msg = (
                'Could not resolve URL for hyperlinked relationship using '
                'view name "%s". You may have failed to include the related '
                'model in your API, or incorrectly configured the '
                '`lookup_field` attribute on this field.'
            )
            raise Exception(msg % view_name)

    def from_native(self, value):
        # Convert URL -> model instance pk
        # TODO: Use values_list
        queryset = self.queryset
        if queryset is None:
            raise Exception('Writable related fields must include a `queryset` argument')

        try:
            http_prefix = value.startswith(('http:', 'https:'))
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

        if match.view_name != self.view_name:
            raise ValidationError(self.error_messages['incorrect_match'])

        try:
            return self.get_object(queryset, match.view_name,
                                   match.args, match.kwargs)
        except (ObjectDoesNotExist, TypeError, ValueError):
            raise ValidationError(self.error_messages['does_not_exist'])


class HyperlinkedIdentityField(Field):
    """
    Represents the instance, or a property on the instance, using hyperlinking.
    """
    lookup_field = 'pk'
    read_only = True

    # These are all pending deprecation
    pk_url_kwarg = 'pk'
    slug_field = 'slug'
    slug_url_kwarg = None  # Defaults to same as `slug_field` unless overridden

    def __init__(self, *args, **kwargs):
        try:
            self.view_name = kwargs.pop('view_name')
        except KeyError:
            msg = "HyperlinkedIdentityField requires 'view_name' argument"
            raise ValueError(msg)

        self.format = kwargs.pop('format', None)
        lookup_field = kwargs.pop('lookup_field', None)
        self.lookup_field = lookup_field or self.lookup_field

        # These are pending deprecation
        if 'pk_url_kwarg' in kwargs:
            msg = 'pk_url_kwarg is pending deprecation. Use lookup_field instead.'
            warnings.warn(msg, PendingDeprecationWarning, stacklevel=2)
        if 'slug_url_kwarg' in kwargs:
            msg = 'slug_url_kwarg is pending deprecation. Use lookup_field instead.'
            warnings.warn(msg, PendingDeprecationWarning, stacklevel=2)
        if 'slug_field' in kwargs:
            msg = 'slug_field is pending deprecation. Use lookup_field instead.'
            warnings.warn(msg, PendingDeprecationWarning, stacklevel=2)

        self.slug_field = kwargs.pop('slug_field', self.slug_field)
        default_slug_kwarg = self.slug_url_kwarg or self.slug_field
        self.pk_url_kwarg = kwargs.pop('pk_url_kwarg', self.pk_url_kwarg)
        self.slug_url_kwarg = kwargs.pop('slug_url_kwarg', default_slug_kwarg)

        super(HyperlinkedIdentityField, self).__init__(*args, **kwargs)

    def field_to_native(self, obj, field_name):
        request = self.context.get('request', None)
        format = self.context.get('format', None)
        view_name = self.view_name

        if request is None:
            warnings.warn("Using `HyperlinkedIdentityField` without including the "
                          "request in the serializer context is deprecated. "
                          "Add `context={'request': request}` when instantiating the serializer.",
                          DeprecationWarning, stacklevel=4)

        # By default use whatever format is given for the current context
        # unless the target is a different type to the source.
        #
        # Eg. Consider a HyperlinkedIdentityField pointing from a json
        # representation to an html property of that representation...
        #
        # '/snippets/1/' should link to '/snippets/1/highlight/'
        # ...but...
        # '/snippets/1/.json' should link to '/snippets/1/highlight/.html'
        if format and self.format and self.format != format:
            format = self.format

        # Return the hyperlink, or error if incorrectly configured.
        try:
            return self.get_url(obj, view_name, request, format)
        except NoReverseMatch:
            msg = (
                'Could not resolve URL for hyperlinked relationship using '
                'view name "%s". You may have failed to include the related '
                'model in your API, or incorrectly configured the '
                '`lookup_field` attribute on this field.'
            )
            raise Exception(msg % view_name)

    def get_url(self, obj, view_name, request, format):
        """
        Given an object, return the URL that hyperlinks to the object.

        May raise a `NoReverseMatch` if the `view_name` and `lookup_field`
        attributes are not configured to correctly match the URL conf.
        """
        lookup_field = getattr(obj, self.lookup_field)
        kwargs = {self.lookup_field: lookup_field}
        try:
            return reverse(view_name, kwargs=kwargs, request=request, format=format)
        except NoReverseMatch:
            pass

        if self.pk_url_kwarg != 'pk':
            # Only try pk lookup if it has been explicitly set.
            # Otherwise, the default `lookup_field = 'pk'` has us covered.
            kwargs = {self.pk_url_kwarg: obj.pk}
            try:
                return reverse(view_name, kwargs=kwargs, request=request, format=format)
            except NoReverseMatch:
                pass

        slug = getattr(obj, self.slug_field, None)
        if slug:
            # Only use slug lookup if a slug field exists on the model
            kwargs = {self.slug_url_kwarg: slug}
            try:
                return reverse(view_name, kwargs=kwargs, request=request, format=format)
            except NoReverseMatch:
                pass

        raise NoReverseMatch()


### Old-style many classes for backwards compat

class ManyRelatedField(RelatedField):
    def __init__(self, *args, **kwargs):
        warnings.warn('`ManyRelatedField()` is deprecated. '
                      'Use `RelatedField(many=True)` instead.',
                       DeprecationWarning, stacklevel=2)
        kwargs['many'] = True
        super(ManyRelatedField, self).__init__(*args, **kwargs)


class ManyPrimaryKeyRelatedField(PrimaryKeyRelatedField):
    def __init__(self, *args, **kwargs):
        warnings.warn('`ManyPrimaryKeyRelatedField()` is deprecated. '
                      'Use `PrimaryKeyRelatedField(many=True)` instead.',
                       DeprecationWarning, stacklevel=2)
        kwargs['many'] = True
        super(ManyPrimaryKeyRelatedField, self).__init__(*args, **kwargs)


class ManySlugRelatedField(SlugRelatedField):
    def __init__(self, *args, **kwargs):
        warnings.warn('`ManySlugRelatedField()` is deprecated. '
                      'Use `SlugRelatedField(many=True)` instead.',
                       DeprecationWarning, stacklevel=2)
        kwargs['many'] = True
        super(ManySlugRelatedField, self).__init__(*args, **kwargs)


class ManyHyperlinkedRelatedField(HyperlinkedRelatedField):
    def __init__(self, *args, **kwargs):
        warnings.warn('`ManyHyperlinkedRelatedField()` is deprecated. '
                      'Use `HyperlinkedRelatedField(many=True)` instead.',
                       DeprecationWarning, stacklevel=2)
        kwargs['many'] = True
        super(ManyHyperlinkedRelatedField, self).__init__(*args, **kwargs)
