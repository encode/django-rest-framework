from __future__ import unicode_literals
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import RegexValidator
from django.forms import ImageField as DjangoImageField
from django.utils import six, timezone
from django.utils.dateparse import parse_date, parse_datetime, parse_time
from django.utils.encoding import is_protected_type, smart_text
from django.utils.translation import ugettext_lazy as _
from rest_framework import ISO_8601
from rest_framework.compat import (
    EmailValidator, MinValueValidator, MaxValueValidator,
    MinLengthValidator, MaxLengthValidator, URLValidator, OrderedDict,
    unicode_repr, unicode_to_repr
)
from rest_framework.exceptions import ValidationError
from rest_framework.settings import api_settings
from rest_framework.utils import html, representation, humanize_datetime
import collections
import copy
import datetime
import decimal
import inspect
import re
import uuid


class empty:
    """
    This class is used to represent no data being provided for a given input
    or output value.

    It is required because `None` may be a valid input or output value.
    """
    pass


def is_simple_callable(obj):
    """
    True if the object is a callable that takes no arguments.
    """
    function = inspect.isfunction(obj)
    method = inspect.ismethod(obj)

    if not (function or method):
        return False

    args, _, _, defaults = inspect.getargspec(obj)
    len_args = len(args) if function else len(args) - 1
    len_defaults = len(defaults) if defaults else 0
    return len_args <= len_defaults


def get_attribute(instance, attrs):
    """
    Similar to Python's built in `getattr(instance, attr)`,
    but takes a list of nested attributes, instead of a single attribute.

    Also accepts either attribute lookup on objects or dictionary lookups.
    """
    for attr in attrs:
        if instance is None:
            # Break out early if we get `None` at any point in a nested lookup.
            return None
        try:
            if isinstance(instance, collections.Mapping):
                instance = instance[attr]
            else:
                instance = getattr(instance, attr)
        except ObjectDoesNotExist:
            return None
        if is_simple_callable(instance):
            instance = instance()
    return instance


def set_value(dictionary, keys, value):
    """
    Similar to Python's built in `dictionary[key] = value`,
    but takes a list of nested keys instead of a single key.

    set_value({'a': 1}, [], {'b': 2}) -> {'a': 1, 'b': 2}
    set_value({'a': 1}, ['x'], 2) -> {'a': 1, 'x': 2}
    set_value({'a': 1}, ['x', 'y'], 2) -> {'a': 1, 'x': {'y': 2}}
    """
    if not keys:
        dictionary.update(value)
        return

    for key in keys[:-1]:
        if key not in dictionary:
            dictionary[key] = {}
        dictionary = dictionary[key]

    dictionary[keys[-1]] = value


class CreateOnlyDefault:
    """
    This class may be used to provide default values that are only used
    for create operations, but that do not return any value for update
    operations.
    """
    def __init__(self, default):
        self.default = default

    def set_context(self, serializer_field):
        self.is_update = serializer_field.parent.instance is not None

    def __call__(self):
        if self.is_update:
            raise SkipField()
        if callable(self.default):
            return self.default()
        return self.default

    def __repr__(self):
        return unicode_to_repr(
            '%s(%s)' % (self.__class__.__name__, unicode_repr(self.default))
        )


class CurrentUserDefault:
    def set_context(self, serializer_field):
        self.user = serializer_field.context['request'].user

    def __call__(self):
        return self.user

    def __repr__(self):
        return unicode_to_repr('%s()' % self.__class__.__name__)


class SkipField(Exception):
    pass


NOT_READ_ONLY_WRITE_ONLY = 'May not set both `read_only` and `write_only`'
NOT_READ_ONLY_REQUIRED = 'May not set both `read_only` and `required`'
NOT_REQUIRED_DEFAULT = 'May not set both `required` and `default`'
USE_READONLYFIELD = 'Field(read_only=True) should be ReadOnlyField'
MISSING_ERROR_MESSAGE = (
    'ValidationError raised by `{class_name}`, but error key `{key}` does '
    'not exist in the `error_messages` dictionary.'
)


class Field(object):
    _creation_counter = 0

    default_error_messages = {
        'required': _('This field is required.'),
        'null': _('This field may not be null.')
    }
    default_validators = []
    default_empty_html = empty
    initial = None

    def __init__(self, read_only=False, write_only=False,
                 required=None, default=empty, initial=empty, source=None,
                 label=None, help_text=None, style=None,
                 error_messages=None, validators=None, allow_null=False):
        self._creation_counter = Field._creation_counter
        Field._creation_counter += 1

        # If `required` is unset, then use `True` unless a default is provided.
        if required is None:
            required = default is empty and not read_only

        # Some combinations of keyword arguments do not make sense.
        assert not (read_only and write_only), NOT_READ_ONLY_WRITE_ONLY
        assert not (read_only and required), NOT_READ_ONLY_REQUIRED
        assert not (required and default is not empty), NOT_REQUIRED_DEFAULT
        assert not (read_only and self.__class__ == Field), USE_READONLYFIELD

        self.read_only = read_only
        self.write_only = write_only
        self.required = required
        self.default = default
        self.source = source
        self.initial = self.initial if (initial is empty) else initial
        self.label = label
        self.help_text = help_text
        self.style = {} if style is None else style
        self.allow_null = allow_null

        if self.default_empty_html is not empty:
            if not required:
                self.default_empty_html = empty
            elif default is not empty:
                self.default_empty_html = default

        if validators is not None:
            self.validators = validators[:]

        # These are set up by `.bind()` when the field is added to a serializer.
        self.field_name = None
        self.parent = None

        # Collect default error message from self and parent classes
        messages = {}
        for cls in reversed(self.__class__.__mro__):
            messages.update(getattr(cls, 'default_error_messages', {}))
        messages.update(error_messages or {})
        self.error_messages = messages

    def bind(self, field_name, parent):
        """
        Initializes the field name and parent for the field instance.
        Called when a field is added to the parent serializer instance.
        """

        # In order to enforce a consistent style, we error if a redundant
        # 'source' argument has been used. For example:
        # my_field = serializer.CharField(source='my_field')
        assert self.source != field_name, (
            "It is redundant to specify `source='%s'` on field '%s' in "
            "serializer '%s', because it is the same as the field name. "
            "Remove the `source` keyword argument." %
            (field_name, self.__class__.__name__, parent.__class__.__name__)
        )

        self.field_name = field_name
        self.parent = parent

        # `self.label` should default to being based on the field name.
        if self.label is None:
            self.label = field_name.replace('_', ' ').capitalize()

        # self.source should default to being the same as the field name.
        if self.source is None:
            self.source = field_name

        # self.source_attrs is a list of attributes that need to be looked up
        # when serializing the instance, or populating the validated data.
        if self.source == '*':
            self.source_attrs = []
        else:
            self.source_attrs = self.source.split('.')

    # .validators is a lazily loaded property, that gets its default
    # value from `get_validators`.
    @property
    def validators(self):
        if not hasattr(self, '_validators'):
            self._validators = self.get_validators()
        return self._validators

    @validators.setter
    def validators(self, validators):
        self._validators = validators

    def get_validators(self):
        return self.default_validators[:]

    def get_initial(self):
        """
        Return a value to use when the field is being returned as a primitive
        value, without any object instance.
        """
        return self.initial

    def get_value(self, dictionary):
        """
        Given the *incoming* primitive data, return the value for this field
        that should be validated and transformed to a native value.
        """
        if html.is_html_input(dictionary):
            # HTML forms will represent empty fields as '', and cannot
            # represent None or False values directly.
            if self.field_name not in dictionary:
                if getattr(self.root, 'partial', False):
                    return empty
                return self.default_empty_html
            ret = dictionary[self.field_name]
            if ret == '' and self.allow_null:
                # If the field is blank, and null is a valid value then
                # determine if we should use null instead.
                return '' if getattr(self, 'allow_blank', False) else None
            return ret
        return dictionary.get(self.field_name, empty)

    def get_attribute(self, instance):
        """
        Given the *outgoing* object instance, return the primitive value
        that should be used for this field.
        """
        try:
            return get_attribute(instance, self.source_attrs)
        except (KeyError, AttributeError) as exc:
            if not self.required and self.default is empty:
                raise SkipField()
            msg = (
                'Got {exc_type} when attempting to get a value for field '
                '`{field}` on serializer `{serializer}`.\nThe serializer '
                'field might be named incorrectly and not match '
                'any attribute or key on the `{instance}` instance.\n'
                'Original exception text was: {exc}.'.format(
                    exc_type=type(exc).__name__,
                    field=self.field_name,
                    serializer=self.parent.__class__.__name__,
                    instance=instance.__class__.__name__,
                    exc=exc
                )
            )
            raise type(exc)(msg)

    def get_default(self):
        """
        Return the default value to use when validating data if no input
        is provided for this field.

        If a default has not been set for this field then this will simply
        return `empty`, indicating that no value should be set in the
        validated data for this field.
        """
        if self.default is empty:
            raise SkipField()
        if callable(self.default):
            if hasattr(self.default, 'set_context'):
                self.default.set_context(self)
            return self.default()
        return self.default

    def validate_empty_values(self, data):
        """
        Validate empty values, and either:

        * Raise `ValidationError`, indicating invalid data.
        * Raise `SkipField`, indicating that the field should be ignored.
        * Return (True, data), indicating an empty value that should be
          returned without any furhter validation being applied.
        * Return (False, data), indicating a non-empty value, that should
          have validation applied as normal.
        """
        if self.read_only:
            return (True, self.get_default())

        if data is empty:
            if getattr(self.root, 'partial', False):
                raise SkipField()
            if self.required:
                self.fail('required')
            return (True, self.get_default())

        if data is None:
            if not self.allow_null:
                self.fail('null')
            return (True, None)

        return (False, data)

    def run_validation(self, data=empty):
        """
        Validate a simple representation and return the internal value.

        The provided data may be `empty` if no representation was included
        in the input.

        May raise `SkipField` if the field should not be included in the
        validated data.
        """
        (is_empty_value, data) = self.validate_empty_values(data)
        if is_empty_value:
            return data
        value = self.to_internal_value(data)
        self.run_validators(value)
        return value

    def run_validators(self, value):
        """
        Test the given value against all the validators on the field,
        and either raise a `ValidationError` or simply return.
        """
        errors = []
        for validator in self.validators:
            if hasattr(validator, 'set_context'):
                validator.set_context(self)

            try:
                validator(value)
            except ValidationError as exc:
                # If the validation error contains a mapping of fields to
                # errors then simply raise it immediately rather than
                # attempting to accumulate a list of errors.
                if isinstance(exc.detail, dict):
                    raise
                errors.extend(exc.detail)
            except DjangoValidationError as exc:
                errors.extend(exc.messages)
        if errors:
            raise ValidationError(errors)

    def to_internal_value(self, data):
        """
        Transform the *incoming* primitive data into a native value.
        """
        raise NotImplementedError(
            '{cls}.to_internal_value() must be implemented.'.format(
                cls=self.__class__.__name__
            )
        )

    def to_representation(self, value):
        """
        Transform the *outgoing* native value into primitive data.
        """
        raise NotImplementedError(
            '{cls}.to_representation() must be implemented.\n'
            'If you are upgrading from REST framework version 2 '
            'you might want `ReadOnlyField`.'.format(
                cls=self.__class__.__name__
            )
        )

    def fail(self, key, **kwargs):
        """
        A helper method that simply raises a validation error.
        """
        try:
            msg = self.error_messages[key]
        except KeyError:
            class_name = self.__class__.__name__
            msg = MISSING_ERROR_MESSAGE.format(class_name=class_name, key=key)
            raise AssertionError(msg)
        message_string = msg.format(**kwargs)
        raise ValidationError(message_string)

    @property
    def root(self):
        """
        Returns the top-level serializer for this field.
        """
        root = self
        while root.parent is not None:
            root = root.parent
        return root

    @property
    def context(self):
        """
        Returns the context as passed to the root serializer on initialization.
        """
        return getattr(self.root, '_context', {})

    def __new__(cls, *args, **kwargs):
        """
        When a field is instantiated, we store the arguments that were used,
        so that we can present a helpful representation of the object.
        """
        instance = super(Field, cls).__new__(cls)
        instance._args = args
        instance._kwargs = kwargs
        return instance

    def __deepcopy__(self, memo):
        """
        When cloning fields we instantiate using the arguments it was
        originally created with, rather than copying the complete state.
        """
        args = copy.deepcopy(self._args)
        kwargs = dict(self._kwargs)
        # Bit ugly, but we need to special case 'validators' as Django's
        # RegexValidator does not support deepcopy.
        # We treat validator callables as immutable objects.
        # See https://github.com/tomchristie/django-rest-framework/issues/1954
        validators = kwargs.pop('validators', None)
        kwargs = copy.deepcopy(kwargs)
        if validators is not None:
            kwargs['validators'] = validators
        return self.__class__(*args, **kwargs)

    def __repr__(self):
        """
        Fields are represented using their initial calling arguments.
        This allows us to create descriptive representations for serializer
        instances that show all the declared fields on the serializer.
        """
        return unicode_to_repr(representation.field_repr(self))


# Boolean types...

class BooleanField(Field):
    default_error_messages = {
        'invalid': _('`{input}` is not a valid boolean.')
    }
    default_empty_html = False
    initial = False
    TRUE_VALUES = set(('t', 'T', 'true', 'True', 'TRUE', '1', 1, True))
    FALSE_VALUES = set(('f', 'F', 'false', 'False', 'FALSE', '0', 0, 0.0, False))

    def __init__(self, **kwargs):
        assert 'allow_null' not in kwargs, '`allow_null` is not a valid option. Use `NullBooleanField` instead.'
        super(BooleanField, self).__init__(**kwargs)

    def to_internal_value(self, data):
        if data in self.TRUE_VALUES:
            return True
        elif data in self.FALSE_VALUES:
            return False
        self.fail('invalid', input=data)

    def to_representation(self, value):
        if value in self.TRUE_VALUES:
            return True
        elif value in self.FALSE_VALUES:
            return False
        return bool(value)


class NullBooleanField(Field):
    default_error_messages = {
        'invalid': _('`{input}` is not a valid boolean.')
    }
    initial = None
    TRUE_VALUES = set(('t', 'T', 'true', 'True', 'TRUE', '1', 1, True))
    FALSE_VALUES = set(('f', 'F', 'false', 'False', 'FALSE', '0', 0, 0.0, False))
    NULL_VALUES = set(('n', 'N', 'null', 'Null', 'NULL', '', None))

    def __init__(self, **kwargs):
        assert 'allow_null' not in kwargs, '`allow_null` is not a valid option.'
        kwargs['allow_null'] = True
        super(NullBooleanField, self).__init__(**kwargs)

    def to_internal_value(self, data):
        if data in self.TRUE_VALUES:
            return True
        elif data in self.FALSE_VALUES:
            return False
        elif data in self.NULL_VALUES:
            return None
        self.fail('invalid', input=data)

    def to_representation(self, value):
        if value in self.NULL_VALUES:
            return None
        if value in self.TRUE_VALUES:
            return True
        elif value in self.FALSE_VALUES:
            return False
        return bool(value)


# String types...

class CharField(Field):
    default_error_messages = {
        'blank': _('This field may not be blank.'),
        'max_length': _('Ensure this field has no more than {max_length} characters.'),
        'min_length': _('Ensure this field has at least {min_length} characters.')
    }
    initial = ''

    def __init__(self, **kwargs):
        self.allow_blank = kwargs.pop('allow_blank', False)
        max_length = kwargs.pop('max_length', None)
        min_length = kwargs.pop('min_length', None)
        super(CharField, self).__init__(**kwargs)
        if max_length is not None:
            message = self.error_messages['max_length'].format(max_length=max_length)
            self.validators.append(MaxLengthValidator(max_length, message=message))
        if min_length is not None:
            message = self.error_messages['min_length'].format(min_length=min_length)
            self.validators.append(MinLengthValidator(min_length, message=message))

    def run_validation(self, data=empty):
        # Test for the empty string here so that it does not get validated,
        # and so that subclasses do not need to handle it explicitly
        # inside the `to_internal_value()` method.
        if data == '':
            if not self.allow_blank:
                self.fail('blank')
            return ''
        return super(CharField, self).run_validation(data)

    def to_internal_value(self, data):
        return six.text_type(data)

    def to_representation(self, value):
        return six.text_type(value)


class EmailField(CharField):
    default_error_messages = {
        'invalid': _('Enter a valid email address.')
    }

    def __init__(self, **kwargs):
        super(EmailField, self).__init__(**kwargs)
        validator = EmailValidator(message=self.error_messages['invalid'])
        self.validators.append(validator)

    def to_internal_value(self, data):
        return six.text_type(data).strip()

    def to_representation(self, value):
        return six.text_type(value).strip()


class RegexField(CharField):
    default_error_messages = {
        'invalid': _('This value does not match the required pattern.')
    }

    def __init__(self, regex, **kwargs):
        super(RegexField, self).__init__(**kwargs)
        validator = RegexValidator(regex, message=self.error_messages['invalid'])
        self.validators.append(validator)


class SlugField(CharField):
    default_error_messages = {
        'invalid': _("Enter a valid 'slug' consisting of letters, numbers, underscores or hyphens.")
    }

    def __init__(self, **kwargs):
        super(SlugField, self).__init__(**kwargs)
        slug_regex = re.compile(r'^[-a-zA-Z0-9_]+$')
        validator = RegexValidator(slug_regex, message=self.error_messages['invalid'])
        self.validators.append(validator)


class URLField(CharField):
    default_error_messages = {
        'invalid': _("Enter a valid URL.")
    }

    def __init__(self, **kwargs):
        super(URLField, self).__init__(**kwargs)
        validator = URLValidator(message=self.error_messages['invalid'])
        self.validators.append(validator)


class UUIDField(Field):
    default_error_messages = {
        'invalid': _('"{value}" is not a valid UUID.'),
    }

    def to_internal_value(self, data):
        if not isinstance(data, uuid.UUID):
            try:
                return uuid.UUID(data)
            except (ValueError, TypeError):
                self.fail('invalid', value=data)
        return data

    def to_representation(self, value):
        return str(value)


# Number types...

class IntegerField(Field):
    default_error_messages = {
        'invalid': _('A valid integer is required.'),
        'max_value': _('Ensure this value is less than or equal to {max_value}.'),
        'min_value': _('Ensure this value is greater than or equal to {min_value}.'),
        'max_string_length': _('String value too large')
    }
    MAX_STRING_LENGTH = 1000  # Guard against malicious string inputs.

    def __init__(self, **kwargs):
        max_value = kwargs.pop('max_value', None)
        min_value = kwargs.pop('min_value', None)
        super(IntegerField, self).__init__(**kwargs)
        if max_value is not None:
            message = self.error_messages['max_value'].format(max_value=max_value)
            self.validators.append(MaxValueValidator(max_value, message=message))
        if min_value is not None:
            message = self.error_messages['min_value'].format(min_value=min_value)
            self.validators.append(MinValueValidator(min_value, message=message))

    def to_internal_value(self, data):
        if isinstance(data, six.text_type) and len(data) > self.MAX_STRING_LENGTH:
            self.fail('max_string_length')

        try:
            data = int(data)
        except (ValueError, TypeError):
            self.fail('invalid')
        return data

    def to_representation(self, value):
        return int(value)


class FloatField(Field):
    default_error_messages = {
        'invalid': _("A valid number is required."),
        'max_value': _('Ensure this value is less than or equal to {max_value}.'),
        'min_value': _('Ensure this value is greater than or equal to {min_value}.'),
        'max_string_length': _('String value too large')
    }
    MAX_STRING_LENGTH = 1000  # Guard against malicious string inputs.

    def __init__(self, **kwargs):
        max_value = kwargs.pop('max_value', None)
        min_value = kwargs.pop('min_value', None)
        super(FloatField, self).__init__(**kwargs)
        if max_value is not None:
            message = self.error_messages['max_value'].format(max_value=max_value)
            self.validators.append(MaxValueValidator(max_value, message=message))
        if min_value is not None:
            message = self.error_messages['min_value'].format(min_value=min_value)
            self.validators.append(MinValueValidator(min_value, message=message))

    def to_internal_value(self, data):
        if isinstance(data, six.text_type) and len(data) > self.MAX_STRING_LENGTH:
            self.fail('max_string_length')

        try:
            return float(data)
        except (TypeError, ValueError):
            self.fail('invalid')

    def to_representation(self, value):
        return float(value)


class DecimalField(Field):
    default_error_messages = {
        'invalid': _('A valid number is required.'),
        'max_value': _('Ensure this value is less than or equal to {max_value}.'),
        'min_value': _('Ensure this value is greater than or equal to {min_value}.'),
        'max_digits': _('Ensure that there are no more than {max_digits} digits in total.'),
        'max_decimal_places': _('Ensure that there are no more than {max_decimal_places} decimal places.'),
        'max_whole_digits': _('Ensure that there are no more than {max_whole_digits} digits before the decimal point.'),
        'max_string_length': _('String value too large')
    }
    MAX_STRING_LENGTH = 1000  # Guard against malicious string inputs.

    coerce_to_string = api_settings.COERCE_DECIMAL_TO_STRING

    def __init__(self, max_digits, decimal_places, coerce_to_string=None, max_value=None, min_value=None, **kwargs):
        self.max_digits = max_digits
        self.decimal_places = decimal_places
        self.coerce_to_string = coerce_to_string if (coerce_to_string is not None) else self.coerce_to_string
        super(DecimalField, self).__init__(**kwargs)
        if max_value is not None:
            message = self.error_messages['max_value'].format(max_value=max_value)
            self.validators.append(MaxValueValidator(max_value, message=message))
        if min_value is not None:
            message = self.error_messages['min_value'].format(min_value=min_value)
            self.validators.append(MinValueValidator(min_value, message=message))

    def to_internal_value(self, data):
        """
        Validates that the input is a decimal number. Returns a Decimal
        instance. Returns None for empty values. Ensures that there are no more
        than max_digits in the number, and no more than decimal_places digits
        after the decimal point.
        """
        data = smart_text(data).strip()
        if len(data) > self.MAX_STRING_LENGTH:
            self.fail('max_string_length')

        try:
            value = decimal.Decimal(data)
        except decimal.DecimalException:
            self.fail('invalid')

        # Check for NaN. It is the only value that isn't equal to itself,
        # so we can use this to identify NaN values.
        if value != value:
            self.fail('invalid')

        # Check for infinity and negative infinity.
        if value in (decimal.Decimal('Inf'), decimal.Decimal('-Inf')):
            self.fail('invalid')

        sign, digittuple, exponent = value.as_tuple()
        decimals = abs(exponent)
        # digittuple doesn't include any leading zeros.
        digits = len(digittuple)
        if decimals > digits:
            # We have leading zeros up to or past the decimal point.  Count
            # everything past the decimal point as a digit.  We do not count
            # 0 before the decimal point as a digit since that would mean
            # we would not allow max_digits = decimal_places.
            digits = decimals
        whole_digits = digits - decimals

        if self.max_digits is not None and digits > self.max_digits:
            self.fail('max_digits', max_digits=self.max_digits)
        if self.decimal_places is not None and decimals > self.decimal_places:
            self.fail('max_decimal_places', max_decimal_places=self.decimal_places)
        if self.max_digits is not None and self.decimal_places is not None and whole_digits > (self.max_digits - self.decimal_places):
            self.fail('max_whole_digits', max_whole_digits=self.max_digits - self.decimal_places)

        return value

    def to_representation(self, value):
        if not isinstance(value, decimal.Decimal):
            value = decimal.Decimal(six.text_type(value).strip())

        context = decimal.getcontext().copy()
        context.prec = self.max_digits
        quantized = value.quantize(
            decimal.Decimal('.1') ** self.decimal_places,
            context=context
        )
        if not self.coerce_to_string:
            return quantized
        return '{0:f}'.format(quantized)


# Date & time fields...

class DateTimeField(Field):
    default_error_messages = {
        'invalid': _('Datetime has wrong format. Use one of these formats instead: {format}'),
        'date': _('Expected a datetime but got a date.'),
    }
    format = api_settings.DATETIME_FORMAT
    input_formats = api_settings.DATETIME_INPUT_FORMATS
    default_timezone = timezone.get_default_timezone() if settings.USE_TZ else None

    def __init__(self, format=empty, input_formats=None, default_timezone=None, *args, **kwargs):
        self.format = format if format is not empty else self.format
        self.input_formats = input_formats if input_formats is not None else self.input_formats
        self.default_timezone = default_timezone if default_timezone is not None else self.default_timezone
        super(DateTimeField, self).__init__(*args, **kwargs)

    def enforce_timezone(self, value):
        """
        When `self.default_timezone` is `None`, always return naive datetimes.
        When `self.default_timezone` is not `None`, always return aware datetimes.
        """
        if (self.default_timezone is not None) and not timezone.is_aware(value):
            return timezone.make_aware(value, self.default_timezone)
        elif (self.default_timezone is None) and timezone.is_aware(value):
            return timezone.make_naive(value, timezone.UTC())
        return value

    def to_internal_value(self, value):
        if isinstance(value, datetime.date) and not isinstance(value, datetime.datetime):
            self.fail('date')

        if isinstance(value, datetime.datetime):
            return self.enforce_timezone(value)

        for format in self.input_formats:
            if format.lower() == ISO_8601:
                try:
                    parsed = parse_datetime(value)
                except (ValueError, TypeError):
                    pass
                else:
                    if parsed is not None:
                        return self.enforce_timezone(parsed)
            else:
                try:
                    parsed = datetime.datetime.strptime(value, format)
                except (ValueError, TypeError):
                    pass
                else:
                    return self.enforce_timezone(parsed)

        humanized_format = humanize_datetime.datetime_formats(self.input_formats)
        self.fail('invalid', format=humanized_format)

    def to_representation(self, value):
        if self.format is None:
            return value

        if self.format.lower() == ISO_8601:
            value = value.isoformat()
            if value.endswith('+00:00'):
                value = value[:-6] + 'Z'
            return value
        return value.strftime(self.format)


class DateField(Field):
    default_error_messages = {
        'invalid': _('Date has wrong format. Use one of these formats instead: {format}'),
        'datetime': _('Expected a date but got a datetime.'),
    }
    format = api_settings.DATE_FORMAT
    input_formats = api_settings.DATE_INPUT_FORMATS

    def __init__(self, format=empty, input_formats=None, *args, **kwargs):
        self.format = format if format is not empty else self.format
        self.input_formats = input_formats if input_formats is not None else self.input_formats
        super(DateField, self).__init__(*args, **kwargs)

    def to_internal_value(self, value):
        if isinstance(value, datetime.datetime):
            self.fail('datetime')

        if isinstance(value, datetime.date):
            return value

        for format in self.input_formats:
            if format.lower() == ISO_8601:
                try:
                    parsed = parse_date(value)
                except (ValueError, TypeError):
                    pass
                else:
                    if parsed is not None:
                        return parsed
            else:
                try:
                    parsed = datetime.datetime.strptime(value, format)
                except (ValueError, TypeError):
                    pass
                else:
                    return parsed.date()

        humanized_format = humanize_datetime.date_formats(self.input_formats)
        self.fail('invalid', format=humanized_format)

    def to_representation(self, value):
        if self.format is None:
            return value

        # Applying a `DateField` to a datetime value is almost always
        # not a sensible thing to do, as it means naively dropping
        # any explicit or implicit timezone info.
        assert not isinstance(value, datetime.datetime), (
            'Expected a `date`, but got a `datetime`. Refusing to coerce, '
            'as this may mean losing timezone information. Use a custom '
            'read-only field and deal with timezone issues explicitly.'
        )

        if self.format.lower() == ISO_8601:
            return value.isoformat()
        return value.strftime(self.format)


class TimeField(Field):
    default_error_messages = {
        'invalid': _('Time has wrong format. Use one of these formats instead: {format}'),
    }
    format = api_settings.TIME_FORMAT
    input_formats = api_settings.TIME_INPUT_FORMATS

    def __init__(self, format=empty, input_formats=None, *args, **kwargs):
        self.format = format if format is not empty else self.format
        self.input_formats = input_formats if input_formats is not None else self.input_formats
        super(TimeField, self).__init__(*args, **kwargs)

    def to_internal_value(self, value):
        if isinstance(value, datetime.time):
            return value

        for format in self.input_formats:
            if format.lower() == ISO_8601:
                try:
                    parsed = parse_time(value)
                except (ValueError, TypeError):
                    pass
                else:
                    if parsed is not None:
                        return parsed
            else:
                try:
                    parsed = datetime.datetime.strptime(value, format)
                except (ValueError, TypeError):
                    pass
                else:
                    return parsed.time()

        humanized_format = humanize_datetime.time_formats(self.input_formats)
        self.fail('invalid', format=humanized_format)

    def to_representation(self, value):
        if self.format is None:
            return value

        # Applying a `TimeField` to a datetime value is almost always
        # not a sensible thing to do, as it means naively dropping
        # any explicit or implicit timezone info.
        assert not isinstance(value, datetime.datetime), (
            'Expected a `time`, but got a `datetime`. Refusing to coerce, '
            'as this may mean losing timezone information. Use a custom '
            'read-only field and deal with timezone issues explicitly.'
        )

        if self.format.lower() == ISO_8601:
            return value.isoformat()
        return value.strftime(self.format)


# Choice types...

class ChoiceField(Field):
    default_error_messages = {
        'invalid_choice': _('`{input}` is not a valid choice.')
    }

    def __init__(self, choices, **kwargs):
        # Allow either single or paired choices style:
        # choices = [1, 2, 3]
        # choices = [(1, 'First'), (2, 'Second'), (3, 'Third')]
        pairs = [
            isinstance(item, (list, tuple)) and len(item) == 2
            for item in choices
        ]
        if all(pairs):
            self.choices = OrderedDict([(key, display_value) for key, display_value in choices])
        else:
            self.choices = OrderedDict([(item, item) for item in choices])

        # Map the string representation of choices to the underlying value.
        # Allows us to deal with eg. integer choices while supporting either
        # integer or string input, but still get the correct datatype out.
        self.choice_strings_to_values = dict([
            (six.text_type(key), key) for key in self.choices.keys()
        ])

        self.allow_blank = kwargs.pop('allow_blank', False)

        super(ChoiceField, self).__init__(**kwargs)

    def to_internal_value(self, data):
        if data == '' and self.allow_blank:
            return ''

        try:
            return self.choice_strings_to_values[six.text_type(data)]
        except KeyError:
            self.fail('invalid_choice', input=data)

    def to_representation(self, value):
        if value in ('', None):
            return value
        return self.choice_strings_to_values[six.text_type(value)]


class MultipleChoiceField(ChoiceField):
    default_error_messages = {
        'invalid_choice': _('`{input}` is not a valid choice.'),
        'not_a_list': _('Expected a list of items but got type `{input_type}`.')
    }
    default_empty_html = []

    def get_value(self, dictionary):
        # We override the default field access in order to support
        # lists in HTML forms.
        if html.is_html_input(dictionary):
            return dictionary.getlist(self.field_name)
        return dictionary.get(self.field_name, empty)

    def to_internal_value(self, data):
        if isinstance(data, type('')) or not hasattr(data, '__iter__'):
            self.fail('not_a_list', input_type=type(data).__name__)

        return set([
            super(MultipleChoiceField, self).to_internal_value(item)
            for item in data
        ])

    def to_representation(self, value):
        return set([
            self.choice_strings_to_values[six.text_type(item)] for item in value
        ])


# File types...

class FileField(Field):
    default_error_messages = {
        'required': _("No file was submitted."),
        'invalid': _("The submitted data was not a file. Check the encoding type on the form."),
        'no_name': _("No filename could be determined."),
        'empty': _("The submitted file is empty."),
        'max_length': _('Ensure this filename has at most {max_length} characters (it has {length}).'),
    }
    use_url = api_settings.UPLOADED_FILES_USE_URL

    def __init__(self, *args, **kwargs):
        self.max_length = kwargs.pop('max_length', None)
        self.allow_empty_file = kwargs.pop('allow_empty_file', False)
        self.use_url = kwargs.pop('use_url', self.use_url)
        super(FileField, self).__init__(*args, **kwargs)

    def to_internal_value(self, data):
        try:
            # `UploadedFile` objects should have name and size attributes.
            file_name = data.name
            file_size = data.size
        except AttributeError:
            self.fail('invalid')

        if not file_name:
            self.fail('no_name')
        if not self.allow_empty_file and not file_size:
            self.fail('empty')
        if self.max_length and len(file_name) > self.max_length:
            self.fail('max_length', max_length=self.max_length, length=len(file_name))

        return data

    def to_representation(self, value):
        if self.use_url:
            if not value:
                return None
            url = value.url
            request = self.context.get('request', None)
            if request is not None:
                return request.build_absolute_uri(url)
            return url
        return value.name


class ImageField(FileField):
    default_error_messages = {
        'invalid_image': _(
            'Upload a valid image. The file you uploaded was either not an '
            'image or a corrupted image.'
        ),
    }

    def __init__(self, *args, **kwargs):
        self._DjangoImageField = kwargs.pop('_DjangoImageField', DjangoImageField)
        super(ImageField, self).__init__(*args, **kwargs)

    def to_internal_value(self, data):
        # Image validation is a bit grungy, so we'll just outright
        # defer to Django's implementation so we don't need to
        # consider it, or treat PIL as a test dependency.
        file_object = super(ImageField, self).to_internal_value(data)
        django_field = self._DjangoImageField()
        django_field.error_messages = self.error_messages
        django_field.to_python(file_object)
        return file_object


# Composite field types...

class _UnvalidatedField(Field):
    def __init__(self, *args, **kwargs):
        super(_UnvalidatedField, self).__init__(*args, **kwargs)
        self.allow_blank = True
        self.allow_null = True

    def to_internal_value(self, data):
        return data

    def to_representation(self, value):
        return value


class ListField(Field):
    child = _UnvalidatedField()
    initial = []
    default_error_messages = {
        'not_a_list': _('Expected a list of items but got type `{input_type}`')
    }

    def __init__(self, *args, **kwargs):
        self.child = kwargs.pop('child', copy.deepcopy(self.child))
        assert not inspect.isclass(self.child), '`child` has not been instantiated.'
        super(ListField, self).__init__(*args, **kwargs)
        self.child.bind(field_name='', parent=self)

    def get_value(self, dictionary):
        # We override the default field access in order to support
        # lists in HTML forms.
        if html.is_html_input(dictionary):
            return html.parse_html_list(dictionary, prefix=self.field_name)
        return dictionary.get(self.field_name, empty)

    def to_internal_value(self, data):
        """
        List of dicts of native values <- List of dicts of primitive datatypes.
        """
        if html.is_html_input(data):
            data = html.parse_html_list(data)
        if isinstance(data, type('')) or not hasattr(data, '__iter__'):
            self.fail('not_a_list', input_type=type(data).__name__)
        return [self.child.run_validation(item) for item in data]

    def to_representation(self, data):
        """
        List of object instances -> List of dicts of primitive datatypes.
        """
        return [self.child.to_representation(item) for item in data]


class DictField(Field):
    child = _UnvalidatedField()
    initial = []
    default_error_messages = {
        'not_a_dict': _('Expected a dictionary of items but got type `{input_type}`')
    }

    def __init__(self, *args, **kwargs):
        self.child = kwargs.pop('child', copy.deepcopy(self.child))
        assert not inspect.isclass(self.child), '`child` has not been instantiated.'
        super(DictField, self).__init__(*args, **kwargs)
        self.child.bind(field_name='', parent=self)

    def get_value(self, dictionary):
        # We override the default field access in order to support
        # lists in HTML forms.
        if html.is_html_input(dictionary):
            return html.parse_html_list(dictionary, prefix=self.field_name)
        return dictionary.get(self.field_name, empty)

    def to_internal_value(self, data):
        """
        Dicts of native values <- Dicts of primitive datatypes.
        """
        if html.is_html_input(data):
            data = html.parse_html_dict(data)
        if not isinstance(data, dict):
            self.fail('not_a_dict', input_type=type(data).__name__)
        return dict([
            (six.text_type(key), self.child.run_validation(value))
            for key, value in data.items()
        ])

    def to_representation(self, value):
        """
        List of object instances -> List of dicts of primitive datatypes.
        """
        return dict([
            (six.text_type(key), self.child.to_representation(val))
            for key, val in value.items()
        ])


# Miscellaneous field types...

class ReadOnlyField(Field):
    """
    A read-only field that simply returns the field value.

    If the field is a method with no parameters, the method will be called
    and it's return value used as the representation.

    For example, the following would call `get_expiry_date()` on the object:

    class ExampleSerializer(self):
        expiry_date = ReadOnlyField(source='get_expiry_date')
    """

    def __init__(self, **kwargs):
        kwargs['read_only'] = True
        super(ReadOnlyField, self).__init__(**kwargs)

    def to_representation(self, value):
        return value


class HiddenField(Field):
    """
    A hidden field does not take input from the user, or present any output,
    but it does populate a field in `validated_data`, based on its default
    value. This is particularly useful when we have a `unique_for_date`
    constraint on a pair of fields, as we need some way to include the date in
    the validated data.
    """
    def __init__(self, **kwargs):
        assert 'default' in kwargs, 'default is a required argument.'
        kwargs['write_only'] = True
        super(HiddenField, self).__init__(**kwargs)

    def get_value(self, dictionary):
        # We always use the default value for `HiddenField`.
        # User input is never provided or accepted.
        return empty

    def to_internal_value(self, data):
        return data


class SerializerMethodField(Field):
    """
    A read-only field that get its representation from calling a method on the
    parent serializer class. The method called will be of the form
    "get_{field_name}", and should take a single argument, which is the
    object being serialized.

    For example:

    class ExampleSerializer(self):
        extra_info = SerializerMethodField()

        def get_extra_info(self, obj):
            return ...  # Calculate some data to return.
    """
    def __init__(self, method_name=None, **kwargs):
        self.method_name = method_name
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(SerializerMethodField, self).__init__(**kwargs)

    def bind(self, field_name, parent):
        # In order to enforce a consistent style, we error if a redundant
        # 'method_name' argument has been used. For example:
        # my_field = serializer.CharField(source='my_field')
        default_method_name = 'get_{field_name}'.format(field_name=field_name)
        assert self.method_name != default_method_name, (
            "It is redundant to specify `%s` on SerializerMethodField '%s' in "
            "serializer '%s', because it is the same as the default method name. "
            "Remove the `method_name` argument." %
            (self.method_name, field_name, parent.__class__.__name__)
        )

        # The method name should default to `get_{field_name}`.
        if self.method_name is None:
            self.method_name = default_method_name

        super(SerializerMethodField, self).bind(field_name, parent)

    def to_representation(self, value):
        method = getattr(self.parent, self.method_name)
        return method(value)


class ModelField(Field):
    """
    A generic field that can be used against an arbitrary model field.

    This is used by `ModelSerializer` when dealing with custom model fields,
    that do not have a serializer field to be mapped to.
    """
    default_error_messages = {
        'max_length': _('Ensure this field has no more than {max_length} characters.'),
    }

    def __init__(self, model_field, **kwargs):
        self.model_field = model_field
        # The `max_length` option is supported by Django's base `Field` class,
        # so we'd better support it here.
        max_length = kwargs.pop('max_length', None)
        super(ModelField, self).__init__(**kwargs)
        if max_length is not None:
            message = self.error_messages['max_length'].format(max_length=max_length)
            self.validators.append(MaxLengthValidator(max_length, message=message))

    def to_internal_value(self, data):
        rel = getattr(self.model_field, 'rel', None)
        if rel is not None:
            return rel.to._meta.get_field(rel.field_name).to_python(data)
        return self.model_field.to_python(data)

    def get_attribute(self, obj):
        # We pass the object instance onto `to_representation`,
        # not just the field attribute.
        return obj

    def to_representation(self, obj):
        value = self.model_field._get_val_from_obj(obj)
        if is_protected_type(value):
            return value
        return self.model_field.value_to_string(obj)
