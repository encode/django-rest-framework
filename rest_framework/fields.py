from django.conf import settings
from django.core import validators
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime, parse_time
from django.utils.encoding import is_protected_type
from django.utils.translation import ugettext_lazy as _
from rest_framework import ISO_8601
from rest_framework.compat import smart_text, EmailValidator, MinValueValidator, MaxValueValidator, URLValidator
from rest_framework.settings import api_settings
from rest_framework.utils import html, representation, humanize_datetime
import datetime
import decimal
import inspect
import re


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
        try:
            instance = getattr(instance, attr)
        except AttributeError as exc:
            try:
                return instance[attr]
            except (KeyError, TypeError):
                raise exc
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


class SkipField(Exception):
    pass


NOT_READ_ONLY_WRITE_ONLY = 'May not set both `read_only` and `write_only`'
NOT_READ_ONLY_REQUIRED = 'May not set both `read_only` and `required`'
NOT_READ_ONLY_DEFAULT = 'May not set both `read_only` and `default`'
NOT_REQUIRED_DEFAULT = 'May not set both `required` and `default`'
MISSING_ERROR_MESSAGE = (
    'ValidationError raised by `{class_name}`, but error key `{key}` does '
    'not exist in the `error_messages` dictionary.'
)


class Field(object):
    _creation_counter = 0

    default_error_messages = {
        'required': _('This field is required.')
    }
    default_validators = []

    def __init__(self, read_only=False, write_only=False,
                 required=None, default=empty, initial=None, source=None,
                 label=None, help_text=None, style=None,
                 error_messages=None, validators=[]):
        self._creation_counter = Field._creation_counter
        Field._creation_counter += 1

        # If `required` is unset, then use `True` unless a default is provided.
        if required is None:
            required = default is empty and not read_only

        # Some combinations of keyword arguments do not make sense.
        assert not (read_only and write_only), NOT_READ_ONLY_WRITE_ONLY
        assert not (read_only and required), NOT_READ_ONLY_REQUIRED
        assert not (read_only and default is not empty), NOT_READ_ONLY_DEFAULT
        assert not (required and default is not empty), NOT_REQUIRED_DEFAULT

        self.read_only = read_only
        self.write_only = write_only
        self.required = required
        self.default = default
        self.source = source
        self.initial = initial
        self.label = label
        self.help_text = help_text
        self.style = {} if style is None else style
        self.validators = validators or self.default_validators[:]

        # Collect default error message from self and parent classes
        messages = {}
        for cls in reversed(self.__class__.__mro__):
            messages.update(getattr(cls, 'default_error_messages', {}))
        messages.update(error_messages or {})
        self.error_messages = messages

    def __new__(cls, *args, **kwargs):
        """
        When a field is instantiated, we store the arguments that were used,
        so that we can present a helpful representation of the object.
        """
        instance = super(Field, cls).__new__(cls)
        instance._args = args
        instance._kwargs = kwargs
        return instance

    def bind(self, field_name, parent, root):
        """
        Setup the context for the field instance.
        """
        self.field_name = field_name
        self.parent = parent
        self.root = root
        self.context = parent.context

        # `self.label` should deafult to being based on the field name.
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

    def get_initial(self):
        """
        Return a value to use when the field is being returned as a primative
        value, without any object instance.
        """
        return self.initial

    def get_value(self, dictionary):
        """
        Given the *incoming* primative data, return the value for this field
        that should be validated and transformed to a native value.
        """
        return dictionary.get(self.field_name, empty)

    def get_attribute(self, instance):
        """
        Given the *outgoing* object instance, return the value for this field
        that should be returned as a primative value.
        """
        return get_attribute(instance, self.source_attrs)

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
        return self.default

    def run_validation(self, data=empty):
        """
        Validate a simple representation and return the internal value.

        The provided data may be `empty` if no representation was included
        in the input.

        May raise `SkipField` if the field should not be included in the
        validated data.
        """
        if data is empty:
            if self.required:
                self.fail('required')
            return self.get_default()

        value = self.to_internal_value(data)
        self.run_validators(value)
        return value

    def run_validators(self, value):
        """
        Test the given value against all the validators on the field,
        and either raise a `ValidationError` or simply return.
        """
        if value in (None, '', [], (), {}):
            return

        errors = []
        for validator in self.validators:
            try:
                validator(value)
            except ValidationError as exc:
                errors.extend(exc.messages)
        if errors:
            raise ValidationError(errors)

    def to_internal_value(self, data):
        """
        Transform the *incoming* primative data into a native value.
        """
        raise NotImplementedError('to_internal_value() must be implemented.')

    def to_representation(self, value):
        """
        Transform the *outgoing* native value into primative data.
        """
        raise NotImplementedError('to_representation() must be implemented.')

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
        raise ValidationError(msg.format(**kwargs))

    def __repr__(self):
        return representation.field_repr(self)


# Boolean types...

class BooleanField(Field):
    default_error_messages = {
        'invalid': _('`{input}` is not a valid boolean.')
    }
    TRUE_VALUES = set(('t', 'T', 'true', 'True', 'TRUE', '1', 1, True))
    FALSE_VALUES = set(('f', 'F', 'false', 'False', 'FALSE', '0', 0, 0.0, False))

    def get_value(self, dictionary):
        if html.is_html_input(dictionary):
            # HTML forms do not send a `False` value on an empty checkbox,
            # so we override the default empty value to be False.
            return dictionary.get(self.field_name, False)
        return dictionary.get(self.field_name, empty)

    def to_internal_value(self, data):
        if data in self.TRUE_VALUES:
            return True
        elif data in self.FALSE_VALUES:
            return False
        self.fail('invalid', input=data)

    def to_representation(self, value):
        if value is None:
            return None
        if value in self.TRUE_VALUES:
            return True
        elif value in self.FALSE_VALUES:
            return False
        return bool(value)


# String types...

class CharField(Field):
    default_error_messages = {
        'blank': _('This field may not be blank.')
    }

    def __init__(self, **kwargs):
        self.allow_blank = kwargs.pop('allow_blank', False)
        self.max_length = kwargs.pop('max_length', None)
        self.min_length = kwargs.pop('min_length', None)
        super(CharField, self).__init__(**kwargs)

    def to_internal_value(self, data):
        if data == '' and not self.allow_blank:
            self.fail('blank')
        if data is None:
            return None
        return str(data)

    def to_representation(self, value):
        if value is None:
            return None
        return str(value)


class EmailField(CharField):
    default_error_messages = {
        'invalid': _('Enter a valid email address.')
    }

    def __init__(self, **kwargs):
        super(EmailField, self).__init__(**kwargs)
        validator = EmailValidator(message=self.error_messages['invalid'])
        self.validators.append(validator)

    def to_internal_value(self, data):
        if data == '' and not self.allow_blank:
            self.fail('blank')
        if data is None:
            return None
        return str(data).strip()

    def to_representation(self, value):
        if value is None:
            return None
        return str(value).strip()


class RegexField(CharField):
    default_error_messages = {
        'invalid': _('This value does not match the required pattern.')
    }

    def __init__(self, regex, **kwargs):
        super(RegexField, self).__init__(**kwargs)
        validator = validators.RegexValidator(regex, message=self.error_messages['invalid'])
        self.validators.append(validator)


class SlugField(CharField):
    default_error_messages = {
        'invalid': _("Enter a valid 'slug' consisting of letters, numbers, underscores or hyphens.")
    }

    def __init__(self, **kwargs):
        super(SlugField, self).__init__(**kwargs)
        slug_regex = re.compile(r'^[-a-zA-Z0-9_]+$')
        validator = validators.RegexValidator(slug_regex, message=self.error_messages['invalid'])
        self.validators.append(validator)


class URLField(CharField):
    default_error_messages = {
        'invalid': _("Enter a valid URL.")
    }

    def __init__(self, **kwargs):
        super(URLField, self).__init__(**kwargs)
        validator = URLValidator(message=self.error_messages['invalid'])
        self.validators.append(validator)


# Number types...

class IntegerField(Field):
    default_error_messages = {
        'invalid': _('A valid integer is required.'),
        'max_value': _('Ensure this value is less than or equal to {max_value}.'),
        'min_value': _('Ensure this value is greater than or equal to {min_value}.'),
    }

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
        try:
            data = int(str(data))
        except (ValueError, TypeError):
            self.fail('invalid')
        return data

    def to_representation(self, value):
        if value is None:
            return None
        return int(value)


class FloatField(Field):
    default_error_messages = {
        'invalid': _("A valid number is required."),
        'max_value': _('Ensure this value is less than or equal to {max_value}.'),
        'min_value': _('Ensure this value is greater than or equal to {min_value}.'),
    }

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

    def to_internal_value(self, value):
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            self.fail('invalid')

    def to_representation(self, value):
        if value is None:
            return None
        return float(value)


class DecimalField(Field):
    default_error_messages = {
        'invalid': _('A valid number is required.'),
        'max_value': _('Ensure this value is less than or equal to {max_value}.'),
        'min_value': _('Ensure this value is greater than or equal to {min_value}.'),
        'max_digits': _('Ensure that there are no more than {max_digits} digits in total.'),
        'max_decimal_places': _('Ensure that there are no more than {max_decimal_places} decimal places.'),
        'max_whole_digits': _('Ensure that there are no more than {max_whole_digits} digits before the decimal point.')
    }

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

    def to_internal_value(self, value):
        """
        Validates that the input is a decimal number. Returns a Decimal
        instance. Returns None for empty values. Ensures that there are no more
        than max_digits in the number, and no more than decimal_places digits
        after the decimal point.
        """
        if value in (None, ''):
            return None

        value = smart_text(value).strip()
        try:
            value = decimal.Decimal(value)
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
        if value in (None, ''):
            return None

        if not isinstance(value, decimal.Decimal):
            value = decimal.Decimal(str(value).strip())

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
        if value in (None, ''):
            return None

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
        if value is None or self.format is None:
            return value

        if isinstance(value, datetime.datetime):
            value = value.date()

        if self.format.lower() == ISO_8601:
            return value.isoformat()
        return value.strftime(self.format)


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
        if value in (None, ''):
            return None

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
        if value is None or self.format is None:
            return value

        if self.format.lower() == ISO_8601:
            ret = value.isoformat()
            if ret.endswith('+00:00'):
                ret = ret[:-6] + 'Z'
            return ret
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
        if value in (None, ''):
            return None

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
        if value is None or self.format is None:
            return value

        if isinstance(value, datetime.datetime):
            value = value.time()

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
            self.choices = dict([(key, display_value) for key, display_value in choices])
        else:
            self.choices = dict([(item, item) for item in choices])

        # Map the string representation of choices to the underlying value.
        # Allows us to deal with eg. integer choices while supporting either
        # integer or string input, but still get the correct datatype out.
        self.choice_strings_to_values = dict([
            (str(key), key) for key in self.choices.keys()
        ])

        super(ChoiceField, self).__init__(**kwargs)

    def to_internal_value(self, data):
        try:
            return self.choice_strings_to_values[str(data)]
        except KeyError:
            self.fail('invalid_choice', input=data)

    def to_representation(self, value):
        return self.choice_strings_to_values[str(value)]


class MultipleChoiceField(ChoiceField):
    default_error_messages = {
        'invalid_choice': _('`{input}` is not a valid choice.'),
        'not_a_list': _('Expected a list of items but got type `{input_type}`')
    }

    def to_internal_value(self, data):
        if isinstance(data, type('')) or not hasattr(data, '__iter__'):
            self.fail('not_a_list', input_type=type(data).__name__)

        return set([
            super(MultipleChoiceField, self).to_internal_value(item)
            for item in data
        ])

    def to_representation(self, value):
        return set([
            self.choice_strings_to_values[str(item)] for item in value
        ])


# File types...

class FileField(Field):
    pass  # TODO


class ImageField(Field):
    pass  # TODO


# Advanced field types...

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
        if is_simple_callable(value):
            return value()
        return value


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
    def __init__(self, method_attr=None, **kwargs):
        self.method_attr = method_attr
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(SerializerMethodField, self).__init__(**kwargs)

    def to_representation(self, value):
        method_attr = self.method_attr
        if method_attr is None:
            method_attr = 'get_{field_name}'.format(field_name=self.field_name)
        method = getattr(self.parent, method_attr)
        return method(value)


class ModelField(Field):
    """
    A generic field that can be used against an arbitrary model field.

    This is used by `ModelSerializer` when dealing with custom model fields,
    that do not have a serializer field to be mapped to.
    """
    def __init__(self, model_field, **kwargs):
        self.model_field = model_field
        kwargs['source'] = '*'
        super(ModelField, self).__init__(**kwargs)

    def to_internal_value(self, data):
        rel = getattr(self.model_field, 'rel', None)
        if rel is not None:
            return rel.to._meta.get_field(rel.field_name).to_python(data)
        return self.model_field.to_python(data)

    def to_representation(self, obj):
        value = self.model_field._get_val_from_obj(obj)
        if is_protected_type(value):
            return value
        return self.model_field.value_to_string(obj)
