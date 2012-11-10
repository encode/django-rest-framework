import copy
import datetime
import inspect
import warnings

from django.core import validators
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.urlresolvers import resolve, get_script_prefix
from django.conf import settings
from django.forms import widgets
from django.forms.models import ModelChoiceIterator
from django.utils.encoding import is_protected_type, smart_unicode
from django.utils.translation import ugettext_lazy as _
from rest_framework.reverse import reverse
from rest_framework.compat import parse_date, parse_datetime
from rest_framework.compat import timezone
from urlparse import urlparse


def is_simple_callable(obj):
    """
    True if the object is a callable that takes no arguments.
    """
    return (
        (inspect.isfunction(obj) and not inspect.getargspec(obj)[0]) or
        (inspect.ismethod(obj) and len(inspect.getargspec(obj)[0]) <= 1)
    )


class Field(object):
    creation_counter = 0
    empty = ''
    type_name = None

    def __init__(self, source=None):
        self.parent = None

        self.creation_counter = Field.creation_counter
        Field.creation_counter += 1

        self.source = source

    def initialize(self, parent, field_name):
        """
        Called to set up a field prior to field_to_native or field_from_native.

        parent - The parent serializer.
        model_field - The model field this field corresponds to, if one exists.
        """
        self.parent = parent
        self.root = parent.root or parent
        self.context = self.root.context

    def field_from_native(self, data, field_name, into):
        """
        Given a dictionary and a field name, updates the dictionary `into`,
        with the field and it's deserialized value.
        """
        return

    def field_to_native(self, obj, field_name):
        """
        Given and object and a field name, returns the value that should be
        serialized for that field.
        """
        if obj is None:
            return self.empty

        if self.source == '*':
            return self.to_native(obj)

        if self.source:
            value = obj
            for component in self.source.split('.'):
                value = getattr(value, component)
                if is_simple_callable(value):
                    value = value()
        else:
            value = getattr(obj, field_name)
        return self.to_native(value)

    def to_native(self, value):
        """
        Converts the field's value into it's simple representation.
        """
        if is_simple_callable(value):
            value = value()

        if is_protected_type(value):
            return value
        elif hasattr(value, '__iter__') and not isinstance(value, (dict, basestring)):
            return [self.to_native(item) for item in value]
        elif isinstance(value, dict):
            return dict(map(self.to_native, (k, v)) for k, v in value.items())
        return smart_unicode(value)

    def attributes(self):
        """
        Returns a dictionary of attributes to be used when serializing to xml.
        """
        if self.type_name:
            return {'type': self.type_name}
        return {}


class WritableField(Field):
    """
    Base for read/write fields.
    """
    default_validators = []
    default_error_messages = {
        'required': _('This field is required.'),
        'invalid': _('Invalid value.'),
    }
    widget = widgets.TextInput
    default = None

    def __init__(self, source=None, read_only=False, required=None,
                 validators=[], error_messages=None, widget=None,
                 default=None, blank=None):

        super(WritableField, self).__init__(source=source)

        self.read_only = read_only
        if required is None:
            self.required = not(read_only)
        else:
            assert not read_only, "Cannot set required=True and read_only=True"
            self.required = required

        messages = {}
        for c in reversed(self.__class__.__mro__):
            messages.update(getattr(c, 'default_error_messages', {}))
        messages.update(error_messages or {})
        self.error_messages = messages

        self.validators = self.default_validators + validators
        self.default = default if default is not None else self.default
        self.blank = blank

        # Widgets are ony used for HTML forms.
        widget = widget or self.widget
        if isinstance(widget, type):
            widget = widget()
        self.widget = widget

    def validate(self, value):
        if value in validators.EMPTY_VALUES and self.required:
            raise ValidationError(self.error_messages['required'])

    def run_validators(self, value):
        if value in validators.EMPTY_VALUES:
            return
        errors = []
        for v in self.validators:
            try:
                v(value)
            except ValidationError as e:
                if hasattr(e, 'code') and e.code in self.error_messages:
                    message = self.error_messages[e.code]
                    if e.params:
                        message = message % e.params
                    errors.append(message)
                else:
                    errors.extend(e.messages)
        if errors:
            raise ValidationError(errors)

    def field_from_native(self, data, field_name, into):
        """
        Given a dictionary and a field name, updates the dictionary `into`,
        with the field and it's deserialized value.
        """
        if self.read_only:
            return

        try:
            native = data[field_name]
        except KeyError:
            if self.default is not None:
                native = self.default
            else:
                if self.required:
                    raise ValidationError(self.error_messages['required'])
                return

        value = self.from_native(native)
        if self.source == '*':
            if value:
                into.update(value)
        else:
            self.validate(value)
            self.run_validators(value)
            into[self.source or field_name] = value

    def from_native(self, value):
        """
        Reverts a simple representation back to the field's value.
        """
        return value


class ModelField(WritableField):
    """
    A generic field that can be used against an arbitrary model field.
    """
    def __init__(self, *args, **kwargs):
        try:
            self.model_field = kwargs.pop('model_field')
        except:
            raise ValueError("ModelField requires 'model_field' kwarg")
        super(ModelField, self).__init__(*args, **kwargs)

    def from_native(self, value):
        rel = getattr(self.model_field, "rel", None)
        if rel is not None:
            return rel.to._meta.get_field(rel.field_name).to_python(value)
        else:
            return self.model_field.to_python(value)

    def field_to_native(self, obj, field_name):
        value = self.model_field._get_val_from_obj(obj)
        if is_protected_type(value):
            return value
        return self.model_field.value_to_string(obj)

    def attributes(self):
        return {
            "type": self.model_field.get_internal_type()
        }

##### Relational fields #####


# Not actually Writable, but subclasses may need to be.
class RelatedField(WritableField):
    """
    Base class for related model fields.

    If not overridden, this represents a to-one relationship, using the unicode
    representation of the target.
    """
    widget = widgets.Select
    cache_choices = False
    empty_label = None
    default_read_only = True  # TODO: Remove this

    def __init__(self, *args, **kwargs):
        self.queryset = kwargs.pop('queryset', None)
        super(RelatedField, self).__init__(*args, **kwargs)
        self.read_only = kwargs.pop('read_only', self.default_read_only)

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

    # def __deepcopy__(self, memo):
    #     result = super(RelatedField, self).__deepcopy__(memo)
    #     result.queryset = result.queryset
    #     return result

    def prepare_value(self, obj):
        return self.to_native(obj)

    def label_from_instance(self, obj):
        """
        Return a readable representation for use with eg. select widgets.
        """
        desc = smart_unicode(obj)
        ident = smart_unicode(self.to_native(obj))
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

    ### Regular serializier stuff...

    def field_to_native(self, obj, field_name):
        value = getattr(obj, self.source or field_name)
        return self.to_native(value)

    def field_from_native(self, data, field_name, into):
        if self.read_only:
            return

        value = data.get(field_name)
        into[(self.source or field_name)] = self.from_native(value)


class ManyRelatedMixin(object):
    """
    Mixin to convert a related field to a many related field.
    """
    widget = widgets.SelectMultiple

    def field_to_native(self, obj, field_name):
        value = getattr(obj, self.source or field_name)
        return [self.to_native(item) for item in value.all()]

    def field_from_native(self, data, field_name, into):
        if self.read_only:
            return

        try:
            # Form data
            value = data.getlist(self.source or field_name)
        except:
            # Non-form data
            value = data.get(self.source or field_name)
        else:
            if value == ['']:
                value = []
        into[field_name] = [self.from_native(item) for item in value]


class ManyRelatedField(ManyRelatedMixin, RelatedField):
    """
    Base class for related model managers.

    If not overridden, this represents a to-many relationship, using the unicode
    representations of the target, and is read-only.
    """
    pass


### PrimaryKey relationships

class PrimaryKeyRelatedField(RelatedField):
    """
    Represents a to-one relationship as a pk value.
    """
    default_read_only = False

    # TODO: Remove these field hacks...
    def prepare_value(self, obj):
        return self.to_native(obj.pk)

    def label_from_instance(self, obj):
        """
        Return a readable representation for use with eg. select widgets.
        """
        desc = smart_unicode(obj)
        ident = smart_unicode(self.to_native(obj.pk))
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
            msg = "Invalid pk '%s' - object does not exist." % smart_unicode(data)
            raise ValidationError(msg)

    def field_to_native(self, obj, field_name):
        try:
            # Prefer obj.serializable_value for performance reasons
            pk = obj.serializable_value(self.source or field_name)
        except AttributeError:
            # RelatedObject (reverse relationship)
            obj = getattr(obj, self.source or field_name)
            return self.to_native(obj.pk)
        # Forward relationship
        return self.to_native(pk)


class ManyPrimaryKeyRelatedField(ManyRelatedField):
    """
    Represents a to-many relationship as a pk value.
    """
    default_read_only = False

    def prepare_value(self, obj):
        return self.to_native(obj.pk)

    def label_from_instance(self, obj):
        """
        Return a readable representation for use with eg. select widgets.
        """
        desc = smart_unicode(obj)
        ident = smart_unicode(self.to_native(obj.pk))
        if desc == ident:
            return desc
        return "%s - %s" % (desc, ident)

    def to_native(self, pk):
        return pk

    def field_to_native(self, obj, field_name):
        try:
            # Prefer obj.serializable_value for performance reasons
            queryset = obj.serializable_value(self.source or field_name)
        except AttributeError:
            # RelatedManager (reverse relationship)
            queryset = getattr(obj, self.source or field_name)
            return [self.to_native(item.pk) for item in queryset.all()]
        # Forward relationship
        return [self.to_native(item.pk) for item in queryset.all()]

    def from_native(self, data):
        if self.queryset is None:
            raise Exception('Writable related fields must include a `queryset` argument')

        try:
            return self.queryset.get(pk=data)
        except ObjectDoesNotExist:
            msg = "Invalid pk '%s' - object does not exist." % smart_unicode(data)
            raise ValidationError(msg)

### Slug relationships


class SlugRelatedField(RelatedField):
    default_read_only = False

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
            raise ValidationError('Object with %s=%s does not exist.' %
                                  (self.slug_field, unicode(data)))


class ManySlugRelatedField(ManyRelatedMixin, SlugRelatedField):
    pass


### Hyperlinked relationships

class HyperlinkedRelatedField(RelatedField):
    """
    Represents a to-one relationship, using hyperlinking.
    """
    pk_url_kwarg = 'pk'
    slug_field = 'slug'
    slug_url_kwarg = None  # Defaults to same as `slug_field` unless overridden
    default_read_only = False

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
            raise ValidationError('Could not resolve URL for field using view name "%s"' % view_name)

        kwargs = {self.slug_url_kwarg: slug}
        try:
            return reverse(self.view_name, kwargs=kwargs, request=request, format=format)
        except:
            pass

        kwargs = {self.pk_url_kwarg: obj.pk, self.slug_url_kwarg: slug}
        try:
            return reverse(self.view_name, kwargs=kwargs, request=request, format=format)
        except:
            pass

        raise ValidationError('Could not resolve URL for field using view name "%s"', view_name)

    def from_native(self, value):
        # Convert URL -> model instance pk
        # TODO: Use values_list
        if self.queryset is None:
            raise Exception('Writable related fields must include a `queryset` argument')

        if value.startswith('http:') or value.startswith('https:'):
            # If needed convert absolute URLs to relative path
            value = urlparse(value).path
            prefix = get_script_prefix()
            if value.startswith(prefix):
                value = '/' + value[len(prefix):]

        try:
            match = resolve(value)
        except:
            raise ValidationError('Invalid hyperlink - No URL match')

        if match.url_name != self.view_name:
            raise ValidationError('Invalid hyperlink - Incorrect URL match')

        pk = match.kwargs.get(self.pk_url_kwarg, None)
        slug = match.kwargs.get(self.slug_url_kwarg, None)

        # Try explicit primary key.
        if pk is not None:
            queryset = self.queryset.filter(pk=pk)
        # Next, try looking up by slug.
        elif slug is not None:
            slug_field = self.get_slug_field()
            queryset = self.queryset.filter(**{slug_field: slug})
        # If none of those are defined, it's an error.
        else:
            raise ValidationError('Invalid hyperlink')

        try:
            obj = queryset.get()
        except ObjectDoesNotExist:
            raise ValidationError('Invalid hyperlink - object does not exist.')
        return obj


class ManyHyperlinkedRelatedField(ManyRelatedMixin, HyperlinkedRelatedField):
    """
    Represents a to-many relationship, using hyperlinking.
    """
    pass


class HyperlinkedIdentityField(Field):
    """
    Represents the instance, or a property on the instance, using hyperlinking.
    """
    pk_url_kwarg = 'pk'
    slug_field = 'slug'
    slug_url_kwarg = None  # Defaults to same as `slug_field` unless overridden

    def __init__(self, *args, **kwargs):
        # TODO: Make view_name mandatory, and have the
        # HyperlinkedModelSerializer set it on-the-fly
        self.view_name = kwargs.pop('view_name', None)
        self.format = kwargs.pop('format', None)

        self.slug_field = kwargs.pop('slug_field', self.slug_field)
        default_slug_kwarg = self.slug_url_kwarg or self.slug_field
        self.pk_url_kwarg = kwargs.pop('pk_url_kwarg', self.pk_url_kwarg)
        self.slug_url_kwarg = kwargs.pop('slug_url_kwarg', default_slug_kwarg)

        super(HyperlinkedIdentityField, self).__init__(*args, **kwargs)

    def field_to_native(self, obj, field_name):
        request = self.context.get('request', None)
        format = self.format or self.context.get('format', None)
        view_name = self.view_name or self.parent.opts.view_name
        kwargs = {self.pk_url_kwarg: obj.pk}
        try:
            return reverse(view_name, kwargs=kwargs, request=request, format=format)
        except:
            pass

        slug = getattr(obj, self.slug_field, None)

        if not slug:
            raise ValidationError('Could not resolve URL for field using view name "%s"' % view_name)

        kwargs = {self.slug_url_kwarg: slug}
        try:
            return reverse(self.view_name, kwargs=kwargs, request=request, format=format)
        except:
            pass

        kwargs = {self.pk_url_kwarg: obj.pk, self.slug_url_kwarg: slug}
        try:
            return reverse(self.view_name, kwargs=kwargs, request=request, format=format)
        except:
            pass

        raise ValidationError('Could not resolve URL for field using view name "%s"', view_name)


##### Typed Fields #####

class BooleanField(WritableField):
    type_name = 'BooleanField'
    widget = widgets.CheckboxInput
    default_error_messages = {
        'invalid': _(u"'%s' value must be either True or False."),
    }
    empty = False

    # Note: we set default to `False` in order to fill in missing value not
    # supplied by html form.  TODO: Fix so that only html form input gets
    # this behavior.
    default = False

    def from_native(self, value):
        if value in ('t', 'True', '1'):
            return True
        if value in ('f', 'False', '0'):
            return False
        return bool(value)


class CharField(WritableField):
    type_name = 'CharField'

    def __init__(self, max_length=None, min_length=None, *args, **kwargs):
        self.max_length, self.min_length = max_length, min_length
        super(CharField, self).__init__(*args, **kwargs)
        if min_length is not None:
            self.validators.append(validators.MinLengthValidator(min_length))
        if max_length is not None:
            self.validators.append(validators.MaxLengthValidator(max_length))

    def validate(self, value):
        """
        Validates that the value is supplied (if required).
        """
        # if empty string and allow blank
        if self.blank and not value:
            return
        else:
            super(CharField, self).validate(value)

    def from_native(self, value):
        if isinstance(value, basestring) or value is None:
            return value
        return smart_unicode(value)


class ChoiceField(WritableField):
    type_name = 'ChoiceField'
    widget = widgets.Select
    default_error_messages = {
        'invalid_choice': _('Select a valid choice. %(value)s is not one of the available choices.'),
    }

    def __init__(self, choices=(), *args, **kwargs):
        super(ChoiceField, self).__init__(*args, **kwargs)
        self.choices = choices

    def _get_choices(self):
        return self._choices

    def _set_choices(self, value):
        # Setting choices also sets the choices on the widget.
        # choices can be any iterable, but we call list() on it because
        # it will be consumed more than once.
        self._choices = self.widget.choices = list(value)

    choices = property(_get_choices, _set_choices)

    def validate(self, value):
        """
        Validates that the input is in self.choices.
        """
        super(ChoiceField, self).validate(value)
        if value and not self.valid_value(value):
            raise ValidationError(self.error_messages['invalid_choice'] % {'value': value})

    def valid_value(self, value):
        """
        Check to see if the provided value is a valid choice.
        """
        for k, v in self.choices:
            if isinstance(v, (list, tuple)):
                # This is an optgroup, so look inside the group for options
                for k2, v2 in v:
                    if value == smart_unicode(k2):
                        return True
            else:
                if value == smart_unicode(k):
                    return True
        return False


class EmailField(CharField):
    type_name = 'EmailField'

    default_error_messages = {
        'invalid': _('Enter a valid e-mail address.'),
    }
    default_validators = [validators.validate_email]

    def from_native(self, value):
        ret = super(EmailField, self).from_native(value)
        if ret is None:
            return None
        return ret.strip()

    def __deepcopy__(self, memo):
        result = copy.copy(self)
        memo[id(self)] = result
        #result.widget = copy.deepcopy(self.widget, memo)
        result.validators = self.validators[:]
        return result


class DateField(WritableField):
    type_name = 'DateField'

    default_error_messages = {
        'invalid': _(u"'%s' value has an invalid date format. It must be "
                     u"in YYYY-MM-DD format."),
        'invalid_date': _(u"'%s' value has the correct format (YYYY-MM-DD) "
                          u"but it is an invalid date."),
    }
    empty = None

    def from_native(self, value):
        if value in validators.EMPTY_VALUES:
            return None

        if isinstance(value, datetime.datetime):
            if timezone and settings.USE_TZ and timezone.is_aware(value):
                # Convert aware datetimes to the default time zone
                # before casting them to dates (#17742).
                default_timezone = timezone.get_default_timezone()
                value = timezone.make_naive(value, default_timezone)
            return value.date()
        if isinstance(value, datetime.date):
            return value

        try:
            parsed = parse_date(value)
            if parsed is not None:
                return parsed
        except ValueError:
            msg = self.error_messages['invalid_date'] % value
            raise ValidationError(msg)

        msg = self.error_messages['invalid'] % value
        raise ValidationError(msg)


class DateTimeField(WritableField):
    type_name = 'DateTimeField'

    default_error_messages = {
        'invalid': _(u"'%s' value has an invalid format. It must be in "
                     u"YYYY-MM-DD HH:MM[:ss[.uuuuuu]][TZ] format."),
        'invalid_date': _(u"'%s' value has the correct format "
                          u"(YYYY-MM-DD) but it is an invalid date."),
        'invalid_datetime': _(u"'%s' value has the correct format "
                              u"(YYYY-MM-DD HH:MM[:ss[.uuuuuu]][TZ]) "
                              u"but it is an invalid date/time."),
    }
    empty = None

    def from_native(self, value):
        if value in validators.EMPTY_VALUES:
            return None

        if isinstance(value, datetime.datetime):
            return value
        if isinstance(value, datetime.date):
            value = datetime.datetime(value.year, value.month, value.day)
            if settings.USE_TZ:
                # For backwards compatibility, interpret naive datetimes in
                # local time. This won't work during DST change, but we can't
                # do much about it, so we let the exceptions percolate up the
                # call stack.
                warnings.warn(u"DateTimeField received a naive datetime (%s)"
                              u" while time zone support is active." % value,
                              RuntimeWarning)
                default_timezone = timezone.get_default_timezone()
                value = timezone.make_aware(value, default_timezone)
            return value

        try:
            parsed = parse_datetime(value)
            if parsed is not None:
                return parsed
        except ValueError:
            msg = self.error_messages['invalid_datetime'] % value
            raise ValidationError(msg)

        try:
            parsed = parse_date(value)
            if parsed is not None:
                return datetime.datetime(parsed.year, parsed.month, parsed.day)
        except ValueError:
            msg = self.error_messages['invalid_date'] % value
            raise ValidationError(msg)

        msg = self.error_messages['invalid'] % value
        raise ValidationError(msg)


class IntegerField(WritableField):
    type_name = 'IntegerField'

    default_error_messages = {
        'invalid': _('Enter a whole number.'),
        'max_value': _('Ensure this value is less than or equal to %(limit_value)s.'),
        'min_value': _('Ensure this value is greater than or equal to %(limit_value)s.'),
    }

    def __init__(self, max_value=None, min_value=None, *args, **kwargs):
        self.max_value, self.min_value = max_value, min_value
        super(IntegerField, self).__init__(*args, **kwargs)

        if max_value is not None:
            self.validators.append(validators.MaxValueValidator(max_value))
        if min_value is not None:
            self.validators.append(validators.MinValueValidator(min_value))

    def from_native(self, value):
        if value in validators.EMPTY_VALUES:
            return None

        try:
            value = int(str(value))
        except (ValueError, TypeError):
            raise ValidationError(self.error_messages['invalid'])
        return value


class FloatField(WritableField):
    type_name = 'FloatField'

    default_error_messages = {
        'invalid': _("'%s' value must be a float."),
    }

    def from_native(self, value):
        if value in validators.EMPTY_VALUES:
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            msg = self.error_messages['invalid'] % value
            raise ValidationError(msg)
