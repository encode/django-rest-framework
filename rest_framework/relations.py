from __future__ import unicode_literals
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.urlresolvers import resolve, get_script_prefix
from django import forms
from django.forms import widgets
from django.forms.models import ModelChoiceIterator
from django.utils.translation import ugettext_lazy as _
from rest_framework.fields import Field, WritableField
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
            warnings.warn('The `null` keyword argument is due to be deprecated. '
                          'Use the `required` keyword argument instead.',
                          PendingDeprecationWarning, stacklevel=2)
            kwargs['required'] = not kwargs.pop('null')

        self.queryset = kwargs.pop('queryset', None)
        self.many = kwargs.pop('many', self.many)
        if self.many:
            self.widget = self.many_widget
            self.form_field_class = self.many_form_field_class

        kwargs['read_only'] = kwargs.pop('read_only', self.read_only)
        super(RelatedField, self).__init__(*args, **kwargs)

    def initialize(self, parent, field_name):
        super(RelatedField, self).initialize(parent, field_name)
        if self.queryset is None and not self.read_only:
            try:
                manager = getattr(self.parent.opts.model, self.source or field_name)
                if hasattr(manager, 'related'):  # Forward
                    self.queryset = manager.related.model._default_manager.all()
                else:  # Reverse
                    self.queryset = manager.field.rel.to._default_manager.all()
            except:
                raise
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
            value = getattr(obj, self.source or field_name)
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
            try:
                # Prefer obj.serializable_value for performance reasons
                queryset = obj.serializable_value(self.source or field_name)
            except AttributeError:
                # RelatedManager (reverse relationship)
                queryset = getattr(obj, self.source or field_name)

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
            return self.to_native(obj.pk)

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
    pk_url_kwarg = 'pk'
    slug_field = 'slug'
    slug_url_kwarg = None  # Defaults to same as `slug_field` unless overridden
    read_only = False

    default_error_messages = {
        'no_match': _('Invalid hyperlink - No URL match'),
        'incorrect_match': _('Invalid hyperlink - Incorrect URL match'),
        'configuration_error': _('Invalid hyperlink due to configuration error'),
        'does_not_exist': _("Invalid hyperlink - object does not exist."),
        'incorrect_type': _('Incorrect type.  Expected url string, received %s.'),
    }

    def __init__(self, *args, **kwargs):
        try:
            self.view_name = kwargs.pop('view_name')
        except:
            raise ValueError("Hyperlinked field requires 'view_name' kwarg")

        self.slug_field = kwargs.pop('slug_field', self.slug_field)
        default_slug_kwarg = self.slug_url_kwarg or self.slug_field
        self.pk_url_kwarg = kwargs.pop('pk_url_kwarg', self.pk_url_kwarg)
        self.slug_url_kwarg = kwargs.pop('slug_url_kwarg', default_slug_kwarg)

        self.format = kwargs.pop('format', None)
        super(HyperlinkedRelatedField, self).__init__(*args, **kwargs)

    def get_slug_field(self):
        """
        Get the name of a slug field to be used to look up by slug.
        """
        return self.slug_field

    def to_native(self, obj):
        view_name = self.view_name
        request = self.context.get('request', None)
        format = self.format or self.context.get('format', None)
        pk = getattr(obj, 'pk', None)
        if pk is None:
            return
        kwargs = {self.pk_url_kwarg: pk}
        try:
            return reverse(view_name, kwargs=kwargs, request=request, format=format)
        except:
            pass

        slug = getattr(obj, self.slug_field, None)

        if not slug:
            raise Exception('Could not resolve URL for field using view name "%s"' % view_name)

        kwargs = {self.slug_url_kwarg: slug}
        try:
            return reverse(view_name, kwargs=kwargs, request=request, format=format)
        except:
            pass

        kwargs = {self.pk_url_kwarg: obj.pk, self.slug_url_kwarg: slug}
        try:
            return reverse(view_name, kwargs=kwargs, request=request, format=format)
        except:
            pass

        raise Exception('Could not resolve URL for field using view name "%s"' % view_name)

    def from_native(self, value):
        # Convert URL -> model instance pk
        # TODO: Use values_list
        if self.queryset is None:
            raise Exception('Writable related fields must include a `queryset` argument')

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
        except:
            raise ValidationError(self.error_messages['no_match'])

        if match.view_name != self.view_name:
            raise ValidationError(self.error_messages['incorrect_match'])

        pk = match.kwargs.get(self.pk_url_kwarg, None)
        slug = match.kwargs.get(self.slug_url_kwarg, None)

        # Try explicit primary key.
        if pk is not None:
            queryset = self.queryset.filter(pk=pk)
        # Next, try looking up by slug.
        elif slug is not None:
            slug_field = self.get_slug_field()
            queryset = self.queryset.filter(**{slug_field: slug})
        # If none of those are defined, it's probably a configuation error.
        else:
            raise ValidationError(self.error_messages['configuration_error'])

        try:
            obj = queryset.get()
        except ObjectDoesNotExist:
            raise ValidationError(self.error_messages['does_not_exist'])
        except (TypeError, ValueError):
            msg = self.error_messages['incorrect_type']
            raise ValidationError(msg % type(value).__name__)

        return obj


class HyperlinkedIdentityField(Field):
    """
    Represents the instance, or a property on the instance, using hyperlinking.
    """
    pk_url_kwarg = 'pk'
    slug_field = 'slug'
    slug_url_kwarg = None  # Defaults to same as `slug_field` unless overridden
    read_only = True

    def __init__(self, *args, **kwargs):
        # TODO: Make view_name mandatory, and have the
        # HyperlinkedModelSerializer set it on-the-fly
        self.view_name = kwargs.pop('view_name', None)
        # Optionally the format of the target hyperlink may be specified
        self.format = kwargs.pop('format', None)

        self.slug_field = kwargs.pop('slug_field', self.slug_field)
        default_slug_kwarg = self.slug_url_kwarg or self.slug_field
        self.pk_url_kwarg = kwargs.pop('pk_url_kwarg', self.pk_url_kwarg)
        self.slug_url_kwarg = kwargs.pop('slug_url_kwarg', default_slug_kwarg)

        super(HyperlinkedIdentityField, self).__init__(*args, **kwargs)

    def field_to_native(self, obj, field_name):
        request = self.context.get('request', None)
        format = self.context.get('format', None)
        view_name = self.view_name or self.parent.opts.view_name
        kwargs = {self.pk_url_kwarg: obj.pk}

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

        try:
            return reverse(view_name, kwargs=kwargs, request=request, format=format)
        except:
            pass

        slug = getattr(obj, self.slug_field, None)

        if not slug:
            raise Exception('Could not resolve URL for field using view name "%s"' % view_name)

        kwargs = {self.slug_url_kwarg: slug}
        try:
            return reverse(view_name, kwargs=kwargs, request=request, format=format)
        except:
            pass

        kwargs = {self.pk_url_kwarg: obj.pk, self.slug_url_kwarg: slug}
        try:
            return reverse(view_name, kwargs=kwargs, request=request, format=format)
        except:
            pass

        raise Exception('Could not resolve URL for field using view name "%s"' % view_name)


### Old-style many classes for backwards compat

class ManyRelatedField(RelatedField):
    def __init__(self, *args, **kwargs):
        warnings.warn('`ManyRelatedField()` is due to be deprecated. '
                      'Use `RelatedField(many=True)` instead.',
                       PendingDeprecationWarning, stacklevel=2)
        kwargs['many'] = True
        super(ManyRelatedField, self).__init__(*args, **kwargs)


class ManyPrimaryKeyRelatedField(PrimaryKeyRelatedField):
    def __init__(self, *args, **kwargs):
        warnings.warn('`ManyPrimaryKeyRelatedField()` is due to be deprecated. '
                      'Use `PrimaryKeyRelatedField(many=True)` instead.',
                       PendingDeprecationWarning, stacklevel=2)
        kwargs['many'] = True
        super(ManyPrimaryKeyRelatedField, self).__init__(*args, **kwargs)


class ManySlugRelatedField(SlugRelatedField):
    def __init__(self, *args, **kwargs):
        warnings.warn('`ManySlugRelatedField()` is due to be deprecated. '
                      'Use `SlugRelatedField(many=True)` instead.',
                       PendingDeprecationWarning, stacklevel=2)
        kwargs['many'] = True
        super(ManySlugRelatedField, self).__init__(*args, **kwargs)


class ManyHyperlinkedRelatedField(HyperlinkedRelatedField):
    def __init__(self, *args, **kwargs):
        warnings.warn('`ManyHyperlinkedRelatedField()` is due to be deprecated. '
                      'Use `HyperlinkedRelatedField(many=True)` instead.',
                       PendingDeprecationWarning, stacklevel=2)
        kwargs['many'] = True
        super(ManyHyperlinkedRelatedField, self).__init__(*args, **kwargs)
