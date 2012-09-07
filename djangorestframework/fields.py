import copy
import datetime
import inspect
import warnings

from django.core import validators
from django.core.exceptions import ValidationError
from django.conf import settings
from django.db import DEFAULT_DB_ALIAS
from django.db.models.related import RelatedObject
from django.utils.encoding import is_protected_type, smart_unicode
from django.utils.translation import ugettext_lazy as _
from djangorestframework.compat import parse_date, parse_datetime
from djangorestframework.compat import timezone


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
    default_validators = []
    default_error_messages = {
        'required': _('This field is required.'),
        'invalid': _('Invalid value.'),
    }
    empty = ''

    def __init__(self, source=None, readonly=False, required=None,
                 validators=[], error_messages=None):
        self.parent = None

        self.creation_counter = Field.creation_counter
        Field.creation_counter += 1

        self.source = source
        self.readonly = readonly
        self.required = not(readonly)

        messages = {}
        for c in reversed(self.__class__.__mro__):
            messages.update(getattr(c, 'default_error_messages', {}))
        messages.update(error_messages or {})
        self.error_messages = messages

        self.validators = self.default_validators + validators

    def initialize(self, parent, model_field=None):
        """
        Called to set up a field prior to field_to_native or field_from_native.

        parent - The parent serializer.
        model_field - The model field this field corrosponds to, if one exists.
        """
        self.parent = parent
        self.root = parent.root or parent
        self.context = self.root.context
        if model_field:
            self.model_field = model_field

    def validate(self, value):
        pass
        # if value in validators.EMPTY_VALUES and self.required:
        #     raise ValidationError(self.error_messages['required'])

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
        if hasattr(self, 'model_field'):
            try:
                return self.model_field.rel.to._meta.get_field(self.model_field.rel.field_name).to_python(value)
            except:
                return self.model_field.to_python(value)
        return value

    def field_to_native(self, obj, field_name):
        """
        Given and object and a field name, returns the value that should be
        serialized for that field.
        """
        if obj is None:
            return self.empty

        if self.source == '*':
            return self.to_native(obj)

        self.obj = obj  # Need to hang onto this in the case of model fields
        if hasattr(self, 'model_field'):
            return self.to_native(self.model_field._get_val_from_obj(obj))

        return self.to_native(getattr(obj, self.source or field_name))

    def to_native(self, value):
        """
        Converts the field's value into it's simple representation.
        """
        if is_simple_callable(value):
            value = value()

        if is_protected_type(value):
            return value
        elif hasattr(self, 'model_field'):
            return self.model_field.value_to_string(self.obj)
        return smart_unicode(value)

    def attributes(self):
        """
        Returns a dictionary of attributes to be used when serializing to xml.
        """
        try:
            return {
                "type": self.model_field.get_internal_type()
            }
        except AttributeError:
            return {}


class RelatedField(Field):
    """
    A base class for model related fields or related managers.

    Subclass this and override `convert` to define custom behaviour when
    serializing related objects.
    """

    def field_to_native(self, obj, field_name):
        obj = getattr(obj, field_name)
        if obj.__class__.__name__ in ('RelatedManager', 'ManyRelatedManager'):
            return [self.to_native(item) for item in obj.all()]
        return self.to_native(obj)

    def attributes(self):
        try:
            return {
                "rel": self.model_field.rel.__class__.__name__,
                "to": smart_unicode(self.model_field.rel.to._meta)
            }
        except AttributeError:
            return {}


class PrimaryKeyRelatedField(RelatedField):
    """
    Serializes a model related field or related manager to a pk value.
    """

    # Note the we use ModelRelatedField's implementation, as we want to get the
    # raw database value directly, since that won't involve another
    # database lookup.
    #
    # An alternative implementation would simply be this...
    #
    # class PrimaryKeyRelatedField(RelatedField):
    #     def to_native(self, obj):
    #         return obj.pk

    def to_native(self, pk):
        """
        Simply returns the object's pk.  You can subclass this method to
        provide different serialization behavior of the pk.
        (For example returning a URL based on the model's pk.)
        """
        return pk

    def field_to_native(self, obj, field_name):
        try:
            obj = obj.serializable_value(field_name)
        except AttributeError:
            field = obj._meta.get_field_by_name(field_name)[0]
            obj = getattr(obj, field_name)
            if obj.__class__.__name__ == 'RelatedManager':
                return [self.to_native(item.pk) for item in obj.all()]
            elif isinstance(field, RelatedObject):
                return self.to_native(obj.pk)
            raise
        if obj.__class__.__name__ == 'ManyRelatedManager':
            return [self.to_native(item.pk) for item in obj.all()]
        return self.to_native(obj)

    def field_from_native(self, data, field_name, into):
        value = data.get(field_name)
        if hasattr(value, '__iter__'):
            into[field_name] = [self.from_native(item) for item in value]
        else:
            into[field_name + '_id'] = self.from_native(value)


class NaturalKeyRelatedField(RelatedField):
    """
    Serializes a model related field or related manager to a natural key value.
    """
    is_natural_key = True  # XML renderer handles these differently

    def to_native(self, obj):
        if hasattr(obj, 'natural_key'):
            return obj.natural_key()
        return obj

    def field_from_native(self, data, field_name, into):
        value = data.get(field_name)
        into[self.model_field.attname] = self.from_native(value)

    def from_native(self, value):
        # TODO: Support 'using' : db = options.pop('using', DEFAULT_DB_ALIAS)
        manager = self.model_field.rel.to._default_manager
        manager = manager.db_manager(DEFAULT_DB_ALIAS)
        return manager.get_by_natural_key(*value).pk


class BooleanField(Field):
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


class CharField(Field):
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


class DateField(Field):
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


class DateTimeField(Field):
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


class IntegerField(Field):
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


class FloatField(Field):
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

# field_mapping = {
#     models.AutoField: IntegerField,
#     models.BooleanField: BooleanField,
#     models.CharField: CharField,
#     models.DateTimeField: DateTimeField,
#     models.DateField: DateField,
#     models.BigIntegerField: IntegerField,
#     models.IntegerField: IntegerField,
#     models.PositiveIntegerField: IntegerField,
#     models.FloatField: FloatField
# }


# def modelfield_to_serializerfield(field):
#     return field_mapping.get(type(field), Field)
