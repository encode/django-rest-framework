from collections import namedtuple
from coreschema.compat import text_types, numeric_types
from coreschema.formats import validate_format
from coreschema.utils import uniq
import re


Error = namedtuple('Error', ['text', 'index'])


def push_index(errors, key):
    return [
        Error(error.text, [key] + error.index)
        for error in errors
    ]


# TODO: Properties as OrderedDict if from list of tuples.
# TODO: null keyword / Nullable
# TODO: dependancies
# TODO: remote ref
# TODO: remaining formats
# LATER: Enum display values
# LATER: File
# LATER: strict, coerce float etc...
# LATER: decimals
# LATER: override errors


class Schema(object):
    errors = {}

    def __init__(self, title='', description='', default=None):
        self.title = title
        self.description = description
        self.default = default

    def make_error(self, code):
        error_string = self.errors[code]
        params = self.__dict__
        return Error(error_string.format(**params), [])

    def __or__(self, other):
        if isinstance(self, Union):
            self_children = self.children
        else:
            self_children = [self]

        if isinstance(other, Union):
            other_children = other.children
        else:
            other_children = [other]

        return Union(self_children + other_children)

    def __and__(self, other):
        if isinstance(self, Intersection):
            self_children = self.children
        else:
            self_children = [self]

        if isinstance(other, Intersection):
            other_children = other.children
        else:
            other_children = [other]

        return Intersection(self_children + other_children)

    def __xor__(self, other):
        return ExclusiveUnion([self, other])

    def __invert__(self):
        return Not(self)

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__ and
            self.__dict__ == other.__dict__
        )


class Object(Schema):
    errors = {
        'type': 'Must be an object.',
        'invalid_key': 'Object keys must be strings.',
        'empty': 'Must not be empty.',
        'required': 'This field is required.',
        'max_properties': 'Must have no more than {max_properties} properties.',
        'min_properties': 'Must have at least {min_properties} properties.',
        'invalid_property': 'Invalid property.'
    }

    def __init__(self, properties=None, required=None, max_properties=None, min_properties=None, pattern_properties=None, additional_properties=True, **kwargs):
        super(Object, self).__init__(**kwargs)

        if isinstance(additional_properties, bool):
            # Handle `additional_properties` set to a boolean.
            self.additional_properties_schema = Anything()
        else:
            # Handle `additional_properties` set to a schema.
            self.additional_properties_schema = additional_properties
            additional_properties = True

        self.properties = properties
        self.required = required or []
        self.max_properties = max_properties
        self.min_properties = min_properties
        self.pattern_properties = pattern_properties
        self.additional_properties = additional_properties

        # Compile pattern regexes.
        self.pattern_properties_regex = None
        if pattern_properties is not None:
            self.pattern_properties_regex = {
                re.compile(key): value
                for key, value
                in pattern_properties.items()
            }

    def validate(self, value, context=None):
        if not isinstance(value, dict):
            return [self.make_error('type')]

        errors = []
        if any(not isinstance(key, text_types) for key in value.keys()):
            errors += [self.make_error('invalid_key')]
        if self.required is not None:
            for key in self.required:
                if key not in value:
                    error_items = [self.make_error('required')]
                    errors += push_index(error_items, key)
        if self.min_properties is not None:
            if len(value) < self.min_properties:
                if self.min_properties == 1:
                    errors += [self.make_error('empty')]
                else:
                    errors += [self.make_error('min_properties')]
        if self.max_properties is not None:
            if len(value) > self.max_properties:
                errors += [self.make_error('max_properties')]

        # Properties
        remaining_keys = set(value.keys())
        if self.properties is not None:
            remaining_keys -= set(self.properties.keys())
            for key, property_item in self.properties.items():
                if key not in value:
                    continue
                error_items = property_item.validate(value[key], context)
                errors += push_index(error_items, key)

        # Pattern properties
        if self.pattern_properties is not None:
            for key in list(remaining_keys):
                for pattern, schema in self.pattern_properties_regex.items():
                    if re.search(pattern, key):
                        error_items = schema.validate(value[key], context)
                        errors += push_index(error_items, key)
                        remaining_keys.discard(key)

        # Additional properties
        if self.additional_properties:
            for key in remaining_keys:
                error_items = self.additional_properties_schema.validate(value[key], context)
                errors += push_index(error_items, key)
        else:
            for key in remaining_keys:
                error_items = [self.make_error('invalid_property')]
                errors += push_index(error_items, key)

        return errors


class Array(Schema):
    errors = {
        'type': 'Must be an array.',
        'empty': 'Must not be empty.',
        'max_items': 'Must have no more than {max_items} items.',
        'min_items': 'Must have at least {min_items} items.',
        'unique': 'Must not contain duplicate items.'
    }

    def __init__(self, items=None, max_items=None, min_items=None, unique_items=False, additional_items=True, **kwargs):
        super(Array, self).__init__(**kwargs)

        if items is None:
            items = Anything()

        if isinstance(items, list) and additional_items is False:
            # Setting additional_items==False implies a value for max_items.
            if max_items is None or max_items > len(items):
                max_items = len(items)

        self.items = items
        self.max_items = max_items
        self.min_items = min_items
        self.unique_items = unique_items
        self.additional_items = additional_items

    def validate(self, value, context=None):
        if not isinstance(value, list):
            return [self.make_error('type')]

        errors = []
        if self.items is not None:
            child_schema = self.items
            is_list = isinstance(self.items, list)
            for idx, item in enumerate(value):
                if is_list:
                    # Case where `items` is a list of schemas.
                    if idx < len(self.items):
                        # Handle each item in the list.
                        child_schema = self.items[idx]
                    else:
                        # Handle any additional items.
                        if isinstance(self.additional_items, bool):
                            break
                        else:
                            child_schema = self.additional_items
                error_items = child_schema.validate(item, context)
                errors += push_index(error_items, idx)
        if self.min_items is not None:
            if len(value) < self.min_items:
                if self.min_items == 1:
                    errors += [self.make_error('empty')]
                else:
                    errors += [self.make_error('min_items')]
        if self.max_items is not None:
            if len(value) > self.max_items:
                errors += [self.make_error('max_items')]
        if self.unique_items:
            if not(uniq(value)):
                errors += [self.make_error('unique')]

        return errors


class Number(Schema):
    integer_only = False
    errors = {
        'type': 'Must be a number.',
        'minimum': 'Must be greater than or equal to {minimum}.',
        'exclusive_minimum': 'Must be greater than {minimum}.',
        'maximum': 'Must be less than or equal to {maximum}.',
        'exclusive_maximum': 'Must be less than {maximum}.',
        'multiple_of': 'Must be a multiple of {multiple_of}.',
    }

    def __init__(self, minimum=None, maximum=None, exclusive_minimum=False, exclusive_maximum=False, multiple_of=None, **kwargs):
        super(Number, self).__init__(**kwargs)
        self.minimum = minimum
        self.maximum = maximum
        self.exclusive_minimum = exclusive_minimum
        self.exclusive_maximum = exclusive_maximum
        self.multiple_of = multiple_of

    def validate(self, value, context=None):
        if isinstance(value, bool):
            # In Python `bool` subclasses `int`, so handle that case explicitly.
            return [self.make_error('type')]
        if not isinstance(value, numeric_types):
            return [self.make_error('type')]
        if self.integer_only and isinstance(value, float) and not value.is_integer():
            return [self.make_error('type')]

        errors = []
        if self.minimum is not None:
            if self.exclusive_minimum:
                if value <= self.minimum:
                    errors += [self.make_error('exclusive_minimum')]
            else:
                if value < self.minimum:
                    errors += [self.make_error('minimum')]
        if self.maximum is not None:
            if self.exclusive_maximum:
                if value >= self.maximum:
                    errors += [self.make_error('exclusive_maximum')]
            else:
                if value > self.maximum:
                    errors += [self.make_error('maximum')]
        if self.multiple_of is not None:
            if isinstance(self.multiple_of, float):
                failed = not (float(value) / self.multiple_of).is_integer()
            else:
                failed = value % self.multiple_of
            if failed:
                errors += [self.make_error('multiple_of')]
        return errors


class Integer(Number):
    errors = {
        'type': 'Must be an integer.',
        'minimum': 'Must be greater than or equal to {minimum}.',
        'exclusive_minimum': 'Must be greater than {minimum}.',
        'maximum': 'Must be less than or equal to {maximum}.',
        'exclusive_maximum': 'Must be less than {maximum}.',
        'multiple_of': 'Must be a multiple of {multiple_of}.',
    }
    integer_only = True


class String(Schema):
    errors = {
        'type': 'Must be a string.',
        'blank': 'Must not be blank.',
        'max_length': 'Must have no more than {max_length} characters.',
        'min_length': 'Must have at least {min_length} characters.',
        'pattern': 'Must match the pattern /{pattern}/.',
        'format': 'Must be a valid {format}.',
    }

    def __init__(self, max_length=None, min_length=None, pattern=None, format=None, **kwargs):
        super(String, self).__init__(**kwargs)
        self.max_length = max_length
        self.min_length = min_length
        self.pattern = pattern
        self.format = format

        self.pattern_regex = None
        if self.pattern is not None:
            self.pattern_regex = re.compile(pattern)

    def validate(self, value, context=None):
        if not isinstance(value, text_types):
            return [self.make_error('type')]

        errors = []
        if self.min_length is not None:
            if len(value) < self.min_length:
                if self.min_length == 1:
                    errors += [self.make_error('blank')]
                else:
                    errors += [self.make_error('min_length')]
        if self.max_length is not None:
            if len(value) > self.max_length:
                errors += [self.make_error('max_length')]
        if self.pattern is not None:
            if not re.search(self.pattern_regex, value):
                errors += [self.make_error('pattern')]
        if self.format is not None:
            if not validate_format(value, self.format):
                errors += [self.make_error('format')]
        return errors


class Boolean(Schema):
    errors = {
        'type': 'Must be a boolean.'
    }

    def validate(self, value, context=None):
        if not isinstance(value, bool):
            return [self.make_error('type')]
        return []


class Null(Schema):
    errors = {
        'type': 'Must be null.'
    }

    def validate(self, value, context=None):
        if value is not None:
            return [self.make_error('type')]
        return []


class Enum(Schema):
    errors = {
        'enum': 'Must be one of {enum}.',
        'exact': 'Must be {exact}.',
    }

    def __init__(self, enum, **kwargs):
        super(Enum, self).__init__(**kwargs)

        self.enum = enum
        if len(enum) == 1:
            self.exact = repr(enum[0])

    def validate(self, value, context=None):
        if value not in self.enum:
            if len(self.enum) == 1:
                return [self.make_error('exact')]
            return [self.make_error('enum')]
        return []


class Anything(Schema):
    errors = {
        'type': 'Must be a valid primitive type.'
    }
    types = text_types + (dict, list, int, float, bool, type(None))

    def validate(self, value, context=None):
        if not isinstance(value, self.types):
            return [self.make_error('type')]

        errors = []
        if isinstance(value, list):
            schema = Array()
            errors += schema.validate(value, context)
        elif isinstance(value, dict):
            schema = Object()
            errors += schema.validate(value, context)
        return errors


# Composites

class Union(Schema):
    errors = {
        'match': 'Must match one of the options.'
    }

    def __init__(self, children, **kwargs):
        super(Union, self).__init__(**kwargs)

        self.children = children

    def validate(self, value, context=None):
        for child in self.children:
            if child.validate(value, context) == []:
                return []
        return [self.make_error('match')]


class Intersection(Schema):
    def __init__(self, children, **kwargs):
        super(Intersection, self).__init__(**kwargs)
        self.children = children

    def validate(self, value, context=None):
        errors = []
        for child in self.children:
            errors.extend(child.validate(value, context))
        return errors


class ExclusiveUnion(Schema):
    errors = {
        'match': 'Must match one of the options.',
        'match_only_one': 'Must match only one of the options.'
    }

    def __init__(self, children, **kwargs):
        super(ExclusiveUnion, self).__init__(**kwargs)

        self.children = children

    def validate(self, value, context=None):
        matches = 0
        for child in self.children:
            if child.validate(value, context) == []:
                matches += 1
        if not matches:
            return [self.make_error('match')]
        elif matches > 1:
            return [self.make_error('match_only_one')]
        return []


class Not(Schema):
    errors = {
        'must_not_match': 'Must not match the option.'
    }

    def __init__(self, child, **kwargs):
        super(Not, self).__init__(**kwargs)
        self.child = child

    def validate(self, value, context=None):
        errors = []
        if self.child.validate(value, context):
            return []
        return [self.make_error('must_not_match')]


# References

class Ref(Schema):
    def __init__(self, ref_name):
        self.ref_name = ref_name

    def dereference(self, context):
        assert isinstance(context, dict)
        assert 'refs' in context
        assert self.ref_name in context['refs']
        return context['refs'][self.ref_name]

    def validate(self, value, context=None):
        schema = self.dereference(context)
        return schema.validate(value, context)


class RefSpace(Schema):
    def __init__(self, refs, root):
        assert root in refs
        self.refs = refs
        self.root = root
        self.root_validator = refs[root]

    def validate(self, value):
        context = {'refs': self.refs}
        return self.root_validator.validate(value, context)
