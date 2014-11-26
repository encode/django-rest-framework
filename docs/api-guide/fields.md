source: fields.py

# Serializer fields

> Each field in a Form class is responsible not only for validating data, but also for "cleaning" it &mdash; normalizing it to a consistent format.
>
> &mdash; [Django documentation][cite]

Serializer fields handle converting between primitive values and internal datatypes.  They also deal with validating input values, as well as retrieving and setting the values from their parent objects.

---

**Note:** The serializer fields are declared in fields.py, but by convention you should import them using `from rest_framework import serializers` and refer to fields as `serializers.<FieldName>`.

---

## Core arguments

Each serializer field class constructor takes at least these arguments.  Some Field classes take additional, field-specific arguments, but the following should always be accepted:

### `source`

The name of the attribute that will be used to populate the field.  May be a method that only takes a `self` argument, such as `Field(source='get_absolute_url')`, or may use dotted notation to traverse attributes, such as `Field(source='user.email')`.

The value `source='*'` has a special meaning, and is used to indicate that the entire object should be passed through to the field.  This can be useful for creating nested representations, or for fields which require access to the complete object in order to determine the output representation.

Defaults to the name of the field.

### `read_only`

Set this to `True` to ensure that the field is used when serializing a representation, but is not used when creating or updating an instance during deserialization.

Defaults to `False`

### `write_only`

Set this to `True` to ensure that the field may be used when updating or creating an instance, but is not included when serializing the representation.

Defaults to `False`

### `required`

Normally an error will be raised if a field is not supplied during deserialization.
Set to false if this field is not required to be present during deserialization.

Defaults to `True`.

### `allow_null`

Normally an error will be raised if `None` is passed to a serializer field. Set this keyword argument to `True` if `None` should be considered a valid value.

Defaults to `False`

### `default`

If set, this gives the default value that will be used for the field if no input value is supplied.  If not set the default behavior is to not populate the attribute at all.

May be set to a function or other callable, in which case the value will be evaluated each time it is used.

Note that setting a `default` value implies that the field is not required. Including both the `default` and `required` keyword arguments is invalid and will raise an error.

### `validators`

A list of validator functions which should be applied to the incoming field input, and which either raise a validation error or simply return. Validator functions should typically raise `serializers.ValidationError`, but Django's built-in `ValidationError` is also supported for compatibility with validators defined in the Django codebase or third party Django packages.

### `error_messages`

A dictionary of error codes to error messages.

### `label`

A short text string that may be used as the name of the field in HTML form fields or other descriptive elements.

### `help_text`

A text string that may be used as a description of the field in HTML form fields or other descriptive elements.

### `initial`

A value that should be used for pre-populating the value of HTML form fields.

### `style`

A dictionary of key-value pairs that can be used to control how renderers should render the field. The API for this should still be considered experimental, and will be formalized with the 3.1 release.

Two options are currently used in HTML form generation, `'input_type'` and `'base_template'`.

    # Use <input type="password"> for the input.
    password = serializers.CharField(
        style={'input_type': 'password'}
    )

    # Use a radio input instead of a select input.
    color_channel = serializers.ChoiceField(
        choices=['red', 'green', 'blue']
        style = {'base_template': 'radio.html'}
    }

**Note**: The `style` argument replaces the old-style version 2.x `widget` keyword argument. Because REST framework 3 now uses templated HTML form generation, the `widget` option that was used to support Django built-in widgets can no longer be supported. Version 3.1 is planned to include public API support for customizing HTML form generation.

---

## Field

A generic, **read-only** field.  You can use this field for any attribute that does not need to support write operations.

For example, using the following model.

    from django.db import models
    from django.utils.timezone import now

    class Account(models.Model):
        owner = models.ForeignKey('auth.user')
        name = models.CharField(max_length=100)
        created = models.DateTimeField(auto_now_add=True)
        payment_expiry = models.DateTimeField()

        def has_expired(self):
            return now() > self.payment_expiry

A serializer definition that looked like this:

    from rest_framework import serializers

    class AccountSerializer(serializers.HyperlinkedModelSerializer):
        expired = serializers.Field(source='has_expired')

        class Meta:
            model = Account
            fields = ('url', 'owner', 'name', 'expired')

Would produce output similar to:

    {
        'url': 'http://example.com/api/accounts/3/',
        'owner': 'http://example.com/api/users/12/',
        'name': 'FooCorp business account',
        'expired': True
    }

By default, the `Field` class will perform a basic translation of the source value into primitive datatypes, falling back to unicode representations of complex datatypes when necessary.

You can customize this  behavior by overriding the `.to_native(self, value)` method.

**TODO**: Note removal of `WritableField`

---

# Boolean fields

## BooleanField

A boolean representation.

Corresponds to `django.db.models.fields.BooleanField`.

## NullBooleanField

A boolean representation that also accepts `None` as a valid value.

Corresponds to `django.db.models.fields.NullBooleanField`.

---

# String fields

## CharField

A text representation. Optionally validates the text to be shorter than `max_length` and longer than `min_length`.

Corresponds to `django.db.models.fields.CharField` or `django.db.models.fields.TextField`.

**Signature:** `CharField(max_length=None, min_length=None, allow_none=False)`

## EmailField

A text representation, validates the text to be a valid e-mail address.

Corresponds to `django.db.models.fields.EmailField`

**Signature:** `EmailField(max_length=None, min_length=None)`

## RegexField

A text representation, that validates the given value matches against a certain regular expression.

The mandatory `regex` argument may either be a string, or a compiled python regular expression object.

Uses Django's `django.core.validators.RegexValidator` for validation.

Corresponds to `django.forms.fields.RegexField`

**Signature:** `RegexField(regex, max_length=None, min_length=None)`

## SlugField

A `RegexField` that validates the input against the pattern `[a-zA-Z0-9_-]+`.

Corresponds to `django.db.models.fields.SlugField`.

**Signature:** `SlugField(max_length=50, min_length=None)`

## URLField

A `RegexField` that validates the input against a URL matching pattern. Expects fully qualified URLs of the form `http://<host>/<path>`.

Corresponds to `django.db.models.fields.URLField`.  Uses Django's `django.core.validators.URLValidator` for validation.

**Signature:** `URLField(max_length=200, min_length=None)`

---

# Numeric fields

## IntegerField

An integer representation.

Has two optional arguments:

- `max_value` Validate that the number provided is no greater than this value.

- `min_value` Validate that the number provided is no less than this value.

Corresponds to `django.db.models.fields.IntegerField`, `django.db.models.fields.SmallIntegerField`, `django.db.models.fields.PositiveIntegerField` and `django.db.models.fields.PositiveSmallIntegerField`.

## FloatField

A floating point representation.

Has two optional arguments:

- `max_value` Validate that the number provided is no greater than this value.

- `min_value` Validate that the number provided is no less than this value.

Corresponds to `django.db.models.fields.FloatField`.

## DecimalField

A decimal representation, represented in Python by a Decimal instance.

Has two required arguments, and three optional arguments:

- `max_digits` The maximum number of digits allowed in the number. Note that this number must be greater than or equal to decimal_places.

- `decimal_places` The number of decimal places to store with the number.

- `coerce_to_string` Set to `True` if string values should be returned for the representation, or `False` if `Decimal` objects should be returned. Defaults to the same value as the `COERCE_DECIMAL_TO_STRING` settings key, which will be `True` unless overridden. If `Decimal` objects are returned by the serializer, then the final output format will be determined by the renderer.

- `max_value` Validate that the number provided is no greater than this value.

- `min_value` Validate that the number provided is no less than this value.

#### Example usage

To validate numbers up to 999 with a resolution of 2 decimal places, you would use:

    serializers.DecimalField(max_digits=5, decimal_places=2)

And to validate numbers up to anything less than one billion with a resolution of 10 decimal places:

    serializers.DecimalField(max_digits=19, decimal_places=10)

This field also takes an optional argument, `coerce_to_string`. If set to `True` the representation will be output as a string. If set to `False` the representation will be left as a `Decimal` instance and the final representation will be determined by the renderer.

If unset, this will default to the same value as the `COERCE_DECIMAL_TO_STRING` setting, which is `True` unless set otherwise.

**Signature:** `DecimalField(max_digits, decimal_places, coerce_to_string=None)`

Corresponds to `django.db.models.fields.DecimalField`.

---

# Date and time fields

## DateTimeField

A date and time representation.

Corresponds to `django.db.models.fields.DateTimeField`.

When using `ModelSerializer` or `HyperlinkedModelSerializer`, note that any model fields with `auto_now=True` or `auto_now_add=True` will use serializer fields that are `read_only=True` by default.

If you want to override this behavior, you'll need to declare the `DateTimeField` explicitly on the serializer.  For example:

    class CommentSerializer(serializers.ModelSerializer):
        created = serializers.DateTimeField()

        class Meta:
            model = Comment

Note that by default, datetime representations are determined by the renderer in use, although this can be explicitly overridden as detailed below.

In the case of JSON this means the default datetime representation uses the [ECMA 262 date time string specification][ecma262].  This is a subset of ISO 8601 which uses millisecond precision, and includes the 'Z' suffix for the UTC timezone, for example: `2013-01-29T12:34:56.123Z`.

**Signature:** `DateTimeField(format=None, input_formats=None)`

* `format` - A string representing the output format.  If not specified, this defaults to the same value as the `DATETIME_FORMAT` settings key, which will be `'iso-8601'` unless set. Setting to a format string indicates that `to_representation` return values should be coerced to string output. Format strings are described below. Setting this value to `None` indicates that Python `datetime` objects should be returned by `to_representation`. In this case the datetime encoding will be determined by the renderer.
* `input_formats` - A list of strings representing the input formats which may be used to parse the date.  If not specified, the `DATETIME_INPUT_FORMATS` setting will be used, which defaults to `['iso-8601']`.

**DateTimeField format strings**: Format strings may either be [Python strftime formats][strftime] which explicitly specify the format, or the special string `'iso-8601'`, which indicates that [ISO 8601][iso8601] style datetimes should be used. (eg `'2013-01-29T12:34:56.000000Z'`)

## DateField

A date representation.

Corresponds to `django.db.models.fields.DateField`

**Signature:** `DateField(format=None, input_formats=None)`

* `format` - A string representing the output format.  If not specified, this defaults to the same value as the `DATE_FORMAT` settings key, which will be `'iso-8601'` unless set. Setting to a format string indicates that `to_representation` return values should be coerced to string output. Format strings are described below. Setting this value to `None` indicates that Python `date` objects should be returned by `to_representation`. In this case the date encoding will be determined by the renderer.
* `input_formats` - A list of strings representing the input formats which may be used to parse the date.  If not specified, the `DATE_INPUT_FORMATS` setting will be used, which defaults to `['iso-8601']`.

**DateField format strings**: Format strings may either be [Python strftime formats][strftime] which explicitly specify the format, or the special string `'iso-8601'`, which indicates that [ISO 8601][iso8601] style dates should be used. (eg `'2013-01-29'`)

## TimeField

A time representation.

Corresponds to `django.db.models.fields.TimeField`

**Signature:** `TimeField(format=None, input_formats=None)`

* `format` - A string representing the output format.  If not specified, this defaults to the same value as the `TIME_FORMAT` settings key, which will be `'iso-8601'` unless set. Setting to a format string indicates that `to_representation` return values should be coerced to string output. Format strings are described below. Setting this value to `None` indicates that Python `time` objects should be returned by `to_representation`. In this case the time encoding will be determined by the renderer.
* `input_formats` - A list of strings representing the input formats which may be used to parse the date.  If not specified, the `TIME_INPUT_FORMATS` setting will be used, which defaults to `['iso-8601']`.

**TimeField format strings**: Format strings may either be [Python strftime formats][strftime] which explicitly specify the format, or the special string `'iso-8601'`, which indicates that [ISO 8601][iso8601] style times should be used. (eg `'12:34:56.000000'`)

---

# Choice selection fields

## ChoiceField

A field that can accept a value out of a limited set of choices. Takes a single mandatory argument.

- `choices` - A list of valid values, or a list of `(key, display_name)` tuples.

**Signature:** `ChoiceField(choices=())`

## MultipleChoiceField

A field that can accept a set of zero, one or many values, chosen from a limited set of choices. Takes a single mandatory argument. `to_internal_representation` returns a `set` containing the selected values.

- `choices` - A list of valid values, or a list of `(key, display_name)` tuples.

**Signature:** `MultipleChoiceField(choices=())`

---

# File upload fields

## FileField

A file representation.  Performs Django's standard FileField validation.

Corresponds to `django.forms.fields.FileField`.

**Signature:** `FileField(max_length=None, allow_empty_file=False, use_url=UPLOADED_FILES_USE_URL)`

 - `max_length` - designates the maximum length for the file name.

 - `allow_empty_file` - designates if empty files are allowed.

- `use_url` - If set to `True` then URL string values will be used for the output representation. If set to `False` then filename string values will be used for the output representation. Defaults to the value of the `UPLOADED_FILES_USE_URL` settings key, which is `True` unless set otherwise.

## ImageField

An image representation. Validates the uploaded file content as matching a known image format.

Corresponds to `django.forms.fields.ImageField`.

Requires either the `Pillow` package or `PIL` package.  The `Pillow` package is recommended, as `PIL` is no longer actively maintained.

Signature and validation is the same as with `FileField`.

---

**Note:** `FileFields` and `ImageFields` are only suitable for use with `MultiPartParser` or `FileUploadParser`. Most parsers, such as e.g. JSON don't support file uploads.
Django's regular [FILE_UPLOAD_HANDLERS] are used for handling uploaded files.

---

# Composite fields

## ListField

**TODO**

---

# Miscellaneous fields

## ReadOnlyField

**TODO**

## HiddenField

**TODO**

## ModelField

A generic field that can be tied to any arbitrary model field.  The `ModelField` class delegates the task of serialization/deserialization to its associated model field.  This field can be used to create serializer fields for custom model fields, without having to create a new custom serializer field.

The `ModelField` class is generally intended for internal use, but can be used by your API if needed.  In order to properly instantiate a `ModelField`, it must be passed a field that is attached to an instantiated model.  For example: `ModelField(model_field=MyModel()._meta.get_field('custom_field'))`

**Signature:** `ModelField(model_field=<Django ModelField instance>)`

## SerializerMethodField

This is a read-only field. It gets its value by calling a method on the serializer class it is attached to. It can be used to add any sort of data to the serialized representation of your object.

The field constructor accepts a single optional argument, which is the name of the method on the serializer to be called. If not included this defaults to `get_<field_name>`.

The method should accept a single argument (in addition to `self`), which is the object being serialized.  It should return whatever you want to be included in the serialized representation of the object.  For example:

    from django.contrib.auth.models import User
    from django.utils.timezone import now
    from rest_framework import serializers

    class UserSerializer(serializers.ModelSerializer):
        days_since_joined = serializers.SerializerMethodField()

        class Meta:
            model = User

        def get_days_since_joined(self, obj):
            return (now() - obj.date_joined).days

---

# Custom fields

If you want to create a custom field, you'll probably want to override either one or both of the `.to_representation()` and `.to_internal_value()` methods.  These two methods are used to convert between the initial datatype, and a primitive, serializable datatype.  Primitive datatypes may be any of a number, string, date/time/datetime or None.  They may also be any list or dictionary like object that only contains other primitive objects.

The `.to_representation()` method is called to convert the initial datatype into a primitive, serializable datatype.  The `to_internal_value()` method is called to restore a primitive datatype into its internal python representation.

## Examples

Let's look at an example of serializing a class that represents an RGB color value:

    class Color(object):
        """
        A color represented in the RGB colorspace.
        """
        def __init__(self, red, green, blue):
            assert(red >= 0 and green >= 0 and blue >= 0)
            assert(red < 256 and green < 256 and blue < 256)
            self.red, self.green, self.blue = red, green, blue

    class ColorField(serializers.Field):
        """
        Color objects are serialized into "rgb(#, #, #)" notation.
        """
        def to_representation(self, obj):
            return "rgb(%d, %d, %d)" % (obj.red, obj.green, obj.blue)

        def to_internal_value(self, data):
            data = data.strip('rgb(').rstrip(')')
            red, green, blue = [int(col) for col in data.split(',')]
            return Color(red, green, blue)


By default field values are treated as mapping to an attribute on the object.  If you need to customize how the field value is accessed and set you need to override `.get_attribute()` and/or `.get_value()`.

As an example, let's create a field that can be used represent the class name of the object being serialized:

    class ClassNameField(serializers.Field):
        def get_attribute(self, obj):
            # We pass the object instance onto `to_representation`,
            # not just the field attribute.
            return obj
 
        def to_representation(self, obj):
            """
            Serialize the object's class name.
            """
            return obj.__class__.__name__

# Third party packages

The following third party packages are also available.

## DRF Compound Fields

The [drf-compound-fields][drf-compound-fields] package provides "compound" serializer fields, such as lists of simple values, which can be described by other fields rather than serializers with the `many=True` option. Also provided are fields for typed dictionaries and values that can be either a specific type or a list of items of that type.

## DRF Extra Fields

The [drf-extra-fields][drf-extra-fields] package provides extra serializer fields for REST framework, including `Base64ImageField` and `PointField` classes.

## django-rest-framework-gis

The [django-rest-framework-gis][django-rest-framework-gis] package provides geographic addons for django rest framework like a  `GeometryField` field and a GeoJSON serializer.

## django-rest-framework-hstore

The [django-rest-framework-hstore][django-rest-framework-hstore] package provides an `HStoreField` to support [django-hstore][django-hstore] `DictionaryField` model field.

[cite]: https://docs.djangoproject.com/en/dev/ref/forms/api/#django.forms.Form.cleaned_data
[FILE_UPLOAD_HANDLERS]: https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-FILE_UPLOAD_HANDLERS
[ecma262]: http://ecma-international.org/ecma-262/5.1/#sec-15.9.1.15
[strftime]: http://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior
[django-widgets]: https://docs.djangoproject.com/en/dev/ref/forms/widgets/
[iso8601]: http://www.w3.org/TR/NOTE-datetime
[drf-compound-fields]: http://drf-compound-fields.readthedocs.org
[drf-extra-fields]: https://github.com/Hipo/drf-extra-fields
[django-rest-framework-gis]: https://github.com/djangonauts/django-rest-framework-gis
[django-rest-framework-hstore]: https://github.com/djangonauts/django-rest-framework-hstore
[django-hstore]: https://github.com/djangonauts/django-hstore
