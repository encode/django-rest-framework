import copy
import datetime
import inspect
import warnings

from django.core import validators
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.urlresolvers import resolve
from django.conf import settings
from django.utils.encoding import is_protected_type, smart_unicode
from django.utils.translation import ugettext_lazy as _
from rest_framework.reverse import reverse
from rest_framework.compat import parse_date, parse_datetime
from rest_framework.compat import timezone


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

    def initialize(self, parent):
        """
        Called to set up a field prior to field_to_native or field_from_native.

        parent - The parent serializer.
        model_field - The model field this field corrosponds to, if one exists.
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

        all_callable = getattr(value, 'all', None)
        if is_simple_callable(all_callable):
            return [self.to_native(item) for item in value.all()]
        elif hasattr(value, '__iter__') and not isinstance(value, (dict, basestring)):
            return [self.to_native(item) for item in value]
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

    def __init__(self, source=None, readonly=False, required=None,
                 validators=[], error_messages=None):
        super(WritableField, self).__init__(source=source)
        self.readonly = readonly
        if required is None:
            self.required = not(readonly)
        else:
            assert not readonly, "Cannot set required=True and readonly=True"
            self.required = required

        messages = {}
        for c in reversed(self.__class__.__mro__):
            messages.update(getattr(c, 'default_error_messages', {}))
        messages.update(error_messages or {})
        self.error_messages = messages

        self.validators = self.default_validators + validators

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
        if self.readonly:
            return

        try:
            native = data[field_name]
        except KeyError:
            return  # TODO Consider validation behaviour, 'required' opt etc...

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
    A generic field that can be used against an arbirtrary model field.
    """
    def __init__(self, *args, **kwargs):
        try:
            self.model_field = kwargs.pop('model_field')
        except:
            raise ValueError("ModelField requires 'model_field' kwarg")
        super(ModelField, self).__init__(*args, **kwargs)

    def from_native(self, value):
        try:
            rel = self.model_field.rel
        except:
            return self.model_field.to_python(value)
        return rel.to._meta.get_field(rel.field_name).to_python(value)

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


class RelatedField(WritableField):
    """
    Base class for related model fields.
    """
    def __init__(self, *args, **kwargs):
        self.queryset = kwargs.pop('queryset', None)
        super(RelatedField, self).__init__(*args, **kwargs)

    def field_to_native(self, obj, field_name):
        value = getattr(obj, self.source or field_name)
        return self.to_native(value)

    def field_from_native(self, data, field_name, into):
        value = data.get(field_name)
        into[(self.source or field_name) + '_id'] = self.from_native(value)


class ManyRelatedMixin(object):
    """
    Mixin to convert a related field to a many related field.
    """
    def field_to_native(self, obj, field_name):
        value = getattr(obj, self.source or field_name)
        return [self.to_native(item) for item in value.all()]

    def field_from_native(self, data, field_name, into):
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
    """
    pass


### PrimaryKey relationships

class PrimaryKeyRelatedField(RelatedField):
    """
    Serializes a related field or related object to a pk value.
    """

    def to_native(self, pk):
        return pk

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
    Serializes a to-many related field or related manager to a pk value.
    """
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


### Hyperlinked relationships

class HyperlinkedRelatedField(RelatedField):
    pk_url_kwarg = 'pk'
    slug_url_kwarg = 'slug'
    slug_field = 'slug'

    def __init__(self, *args, **kwargs):
        try:
            self.view_name = kwargs.pop('view_name')
        except:
            raise ValueError("Hyperlinked field requires 'view_name' kwarg")
        super(HyperlinkedRelatedField, self).__init__(*args, **kwargs)

    def to_native(self, obj):
        view_name = self.view_name
        request = self.context.get('request', None)
        kwargs = {self.pk_url_kwarg: obj.pk}
        try:
            return reverse(view_name, kwargs=kwargs, request=request)
        except:
            pass

        slug = getattr(obj, self.slug_field, None)

        if not slug:
            raise ValidationError('Could not resolve URL for field using view name "%s"' % view_name)

        kwargs = {self.slug_url_kwarg: slug}
        try:
            return reverse(self.view_name, kwargs=kwargs, request=request)
        except:
            pass

        kwargs = {self.pk_url_kwarg: obj.pk, self.slug_url_kwarg: slug}
        try:
            return reverse(self.view_name, kwargs=kwargs, request=request)
        except:
            pass

        raise ValidationError('Could not resolve URL for field using view name "%s"', view_name)

    def from_native(self, value):
        # Convert URL -> model instance pk
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
            return pk
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
        return obj.pk


class ManyHyperlinkedRelatedField(ManyRelatedMixin, HyperlinkedRelatedField):
    pass


class HyperlinkedIdentityField(Field):
    """
    A field that represents the model's identity using a hyperlink.
    """
    def __init__(self, *args, **kwargs):
        try:
            self.view_name = kwargs.pop('view_name')
        except:
            raise ValueError("Hyperlinked field requires 'view_name' kwarg")
        super(HyperlinkedRelatedField, self).__init__(*args, **kwargs)

    def field_to_native(self, obj, field_name):
        request = self.context.get('request', None)
        view_name = self.view_name or self.parent.opts.view_name
        view_kwargs = {'pk': obj.pk}
        return reverse(view_name, kwargs=view_kwargs, request=request)


##### Typed Fields #####

class BooleanField(WritableField):
    type_name = 'BooleanField'
    default_error_messages = {
        'invalid': _(u"'%s' value must be either True or False."),
    }

    def from_native(self, value):
        if value in (True, False):
            # if value is 1 or 0 than it's equal to True or False, but we want
            # to return a true bool for semantic reasons.
            return bool(value)
        if value in ('t', 'True', '1'):
            return True
        if value in ('f', 'False', '0'):
            return False
        raise ValidationError(self.error_messages['invalid'] % value)


class CharField(WritableField):
    type_name = 'CharField'

    def __init__(self, max_length=None, min_length=None, *args, **kwargs):
        self.max_length, self.min_length = max_length, min_length
        super(CharField, self).__init__(*args, **kwargs)
        if min_length is not None:
            self.validators.append(validators.MinLengthValidator(min_length))
        if max_length is not None:
            self.validators.append(validators.MaxLengthValidator(max_length))

    def from_native(self, value):
        if isinstance(value, basestring) or value is None:
            return value
        return smart_unicode(value)


class EmailField(CharField):
    type_name = 'EmailField'

    default_error_messages = {
        'invalid': _('Enter a valid e-mail address.'),
    }
    default_validators = [validators.validate_email]

    def from_native(self, value):
        return super(EmailField, self).from_native(value).strip()

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
        if value is None:
            return value
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
        if value is None:
            return value
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
        if value is None:
            return value
        try:
            return float(value)
        except (TypeError, ValueError):
            msg = self.error_messages['invalid'] % value
            raise ValidationError(msg)
