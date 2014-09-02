from rest_framework.utils import html
import inspect


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
    """
    for attr in attrs:
        instance = getattr(instance, attr)
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


class ValidationError(Exception):
    pass


class SkipField(Exception):
    pass


class Field(object):
    _creation_counter = 0

    MESSAGES = {
        'required': 'This field is required.'
    }

    _NOT_READ_ONLY_WRITE_ONLY = 'May not set both `read_only` and `write_only`'
    _NOT_READ_ONLY_REQUIRED = 'May not set both `read_only` and `required`'
    _NOT_READ_ONLY_DEFAULT = 'May not set both `read_only` and `default`'
    _NOT_REQUIRED_DEFAULT = 'May not set both `required` and `default`'
    _MISSING_ERROR_MESSAGE = (
        'ValidationError raised by `{class_name}`, but error key `{key}` does '
        'not exist in the `MESSAGES` dictionary.'
    )

    def __init__(self, read_only=False, write_only=False,
                 required=None, default=empty, initial=None, source=None,
                 label=None, style=None, error_messages=None):
        self._creation_counter = Field._creation_counter
        Field._creation_counter += 1

        # If `required` is unset, then use `True` unless a default is provided.
        if required is None:
            required = default is empty and not read_only

        # Some combinations of keyword arguments do not make sense.
        assert not (read_only and write_only), self._NOT_READ_ONLY_WRITE_ONLY
        assert not (read_only and required), self._NOT_READ_ONLY_REQUIRED
        assert not (read_only and default is not empty), self._NOT_READ_ONLY_DEFAULT
        assert not (required and default is not empty), self._NOT_REQUIRED_DEFAULT

        self.read_only = read_only
        self.write_only = write_only
        self.required = required
        self.default = default
        self.source = source
        self.initial = initial
        self.label = label
        self.style = {} if style is None else style

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
            self.label = self.field_name.replace('_', ' ').capitalize()

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

    def validate(self, data=empty):
        """
        Validate a simple representation and return the internal value.

        The provided data may be `empty` if no representation was included.
        May return `empty` if the field should not be included in the
        validated data.
        """
        if data is empty:
            if self.required:
                self.fail('required')
            return self.get_default()

        return self.to_native(data)

    def to_native(self, data):
        """
        Transform the *incoming* primative data into a native value.
        """
        return data

    def to_primative(self, value):
        """
        Transform the *outgoing* native value into primative data.
        """
        return value

    def fail(self, key, **kwargs):
        """
        A helper method that simply raises a validation error.
        """
        try:
            raise ValidationError(self.MESSAGES[key].format(**kwargs))
        except KeyError:
            class_name = self.__class__.__name__
            msg = self._MISSING_ERROR_MESSAGE.format(class_name=class_name, key=key)
            raise AssertionError(msg)


class BooleanField(Field):
    MESSAGES = {
        'required': 'This field is required.',
        'invalid_value': '`{input}` is not a valid boolean.'
    }
    TRUE_VALUES = {'t', 'T', 'true', 'True', 'TRUE', '1', 1, True}
    FALSE_VALUES = {'f', 'F', 'false', 'False', 'FALSE', '0', 0, 0.0, False}

    def get_value(self, dictionary):
        if html.is_html_input(dictionary):
            # HTML forms do not send a `False` value on an empty checkbox,
            # so we override the default empty value to be False.
            return dictionary.get(self.field_name, False)
        return dictionary.get(self.field_name, empty)

    def to_native(self, data):
        if data in self.TRUE_VALUES:
            return True
        elif data in self.FALSE_VALUES:
            return False
        self.fail('invalid_value', input=data)


class CharField(Field):
    MESSAGES = {
        'required': 'This field is required.',
        'blank': 'This field may not be blank.'
    }

    def __init__(self, **kwargs):
        self.allow_blank = kwargs.pop('allow_blank', False)
        self.max_length = kwargs.pop('max_length', None)
        self.min_length = kwargs.pop('min_length', None)
        super(CharField, self).__init__(**kwargs)

    def to_native(self, data):
        if data == '' and not self.allow_blank:
            self.fail('blank')
        return str(data)


class ChoiceField(Field):
    MESSAGES = {
        'required': 'This field is required.',
        'invalid_choice': '`{input}` is not a valid choice.'
    }
    coerce_to_type = str

    def __init__(self, **kwargs):
        choices = kwargs.pop('choices')

        assert choices, '`choices` argument is required and may not be empty'

        # Allow either single or paired choices style:
        # choices = [1, 2, 3]
        # choices = [(1, 'First'), (2, 'Second'), (3, 'Third')]
        pairs = [
            isinstance(item, (list, tuple)) and len(item) == 2
            for item in choices
        ]
        if all(pairs):
            self.choices = {key: val for key, val in choices}
        else:
            self.choices = {item: item for item in choices}

        # Map the string representation of choices to the underlying value.
        # Allows us to deal with eg. integer choices while supporting either
        # integer or string input, but still get the correct datatype out.
        self.choice_strings_to_values = {
            str(key): key for key in self.choices.keys()
        }

        super(ChoiceField, self).__init__(**kwargs)

    def to_native(self, data):
        try:
            return self.choice_strings_to_values[str(data)]
        except KeyError:
            self.fail('invalid_choice', input=data)


class MultipleChoiceField(ChoiceField):
    MESSAGES = {
        'required': 'This field is required.',
        'invalid_choice': '`{input}` is not a valid choice.',
        'not_a_list': 'Expected a list of items but got type `{input_type}`'
    }

    def to_native(self, data):
        if not hasattr(data, '__iter__'):
            self.fail('not_a_list', input_type=type(data).__name__)
        return set([
            super(MultipleChoiceField, self).to_native(item)
            for item in data
        ])


class IntegerField(Field):
    MESSAGES = {
        'required': 'This field is required.',
        'invalid_integer': 'A valid integer is required.'
    }

    def to_native(self, data):
        try:
            data = int(str(data))
        except (ValueError, TypeError):
            self.fail('invalid_integer')
        return data

    def to_primative(self, value):
        if value is None:
            return None
        return int(value)


class EmailField(CharField):
    pass  # TODO


class URLField(CharField):
    pass  # TODO


class RegexField(CharField):
    def __init__(self, **kwargs):
        self.regex = kwargs.pop('regex')
        super(CharField, self).__init__(**kwargs)


class DateField(CharField):
    def __init__(self, **kwargs):
        self.input_formats = kwargs.pop('input_formats', None)
        super(DateField, self).__init__(**kwargs)


class TimeField(CharField):
    def __init__(self, **kwargs):
        self.input_formats = kwargs.pop('input_formats', None)
        super(TimeField, self).__init__(**kwargs)


class DateTimeField(CharField):
    def __init__(self, **kwargs):
        self.input_formats = kwargs.pop('input_formats', None)
        super(DateTimeField, self).__init__(**kwargs)


class FileField(Field):
    pass  # TODO


class ReadOnlyField(Field):
    def to_primative(self, value):
        if is_simple_callable(value):
            return value()
        return value


class MethodField(Field):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(MethodField, self).__init__(**kwargs)

    def to_primative(self, value):
        attr = 'get_{field_name}'.format(field_name=self.field_name)
        method = getattr(self.parent, attr)
        return method(value)
