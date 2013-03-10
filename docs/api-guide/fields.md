<a class="github" href="fields.py"></a>

# Serializer fields

> Each field in a Form class is responsible not only for validating data, but also for "cleaning" it &mdash; normalizing it to a consistent format. 
>
> &mdash; [Django documentation][cite]

Serializer fields handle converting between primitive values and internal datatypes.  They also deal with validating input values, as well as retrieving and setting the values from their parent objects.

---

**Note:** The serializer fields are declared in fields.py, but by convention you should import them using `from rest_framework import serializers` and refer to fields as `serializers.<FieldName>`.

---

## Core arguments

Each serializer field class constructor takes at least these arguments. Some Field classes take additional, field-specific arguments, but the following should always be accepted:

### `source`

The name of the attribute that will be used to populate the field.  May be a method that only takes a `self` argument, such as `Field(source='get_absolute_url')`, or may use dotted notation to traverse attributes, such as `Field(source='user.email')`.

The value `source='*'` has a special meaning, and is used to indicate that the entire object should be passed through to the field.  This can be useful for creating nested representations.  (See the implementation of the `PaginationSerializer` class for an example.)

Defaults to the name of the field.

### `read_only`

Set this to `True` to ensure that the field is used when serializing a representation, but is not used when updating an instance during deserialization.

Defaults to `False`

### `required`

Normally an error will be raised if a field is not supplied during deserialization.
Set to false if this field is not required to be present during deserialization.

Defaults to `True`.

### `default`

If set, this gives the default value that will be used for the field if none is supplied.  If not set the default behavior is to not populate the attribute at all.

### `validators`

A list of Django validators that should be used to validate deserialized values.

### `error_messages`

A dictionary of error codes to error messages.

### `widget`

Used only if rendering the field to HTML.
This argument sets the widget that should be used to render the field.


---

# Generic Fields

These generic fields are used for representing arbitrary model fields or the output of model methods.

## Field

A generic, **read-only** field.  You can use this field for any attribute that does not need to support write operations.

For example, using the following model.

    class Account(models.Model):
        owner = models.ForeignKey('auth.user')
        name = models.CharField(max_length=100)
        created = models.DateTimeField(auto_now_add=True)
        payment_expiry = models.DateTimeField()
        
        def has_expired(self):
            now = datetime.datetime.now()
            return now > self.payment_expiry

A serializer definition that looked like this:

    class AccountSerializer(serializers.HyperlinkedModelSerializer):
        expired = Field(source='has_expired')
        
        class Meta:
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

## WritableField

A field that supports both read and write operations.  By itself `WritableField` does not perform any translation of input values into a given type.  You won't typically use this field directly, but you may want to override it and implement the `.to_native(self, value)` and `.from_native(self, value)` methods.

## ModelField

A generic field that can be tied to any arbitrary model field.  The `ModelField` class delegates the task of serialization/deserialization to it's associated model field.  This field can be used to create serializer fields for custom model fields, without having to create a new custom serializer field.

**Signature:** `ModelField(model_field=<Django ModelField class>)`

## SerializerMethodField

This is a read-only field. It gets its value by calling a method on the serializer class it is attached to. It can be used to add any sort of data to the serialized representation of your object. The field's constructor accepts a single argument, which is the name of the method on the serializer to be called. The method should accept a single argument (in addition to `self`), which is the object being serialized. It should return whatever you want to be included in the serialized representation of the object. For example:

    from rest_framework import serializers
    from django.contrib.auth.models import User
    from django.utils.timezone import now

    class UserSerializer(serializers.ModelSerializer):

        days_since_joined = serializers.SerializerMethodField('get_days_since_joined')

        class Meta:
            model = User

        def get_days_since_joined(self, obj):
            return (now() - obj.date_joined).days

---

# Typed Fields

These fields represent basic datatypes, and support both reading and writing values.

## BooleanField

A Boolean representation.

Corresponds to `django.db.models.fields.BooleanField`.

## CharField

A text representation, optionally validates the text to be shorter than `max_length` and longer than `min_length`.

Corresponds to `django.db.models.fields.CharField`
or `django.db.models.fields.TextField`.

**Signature:** `CharField(max_length=None, min_length=None)`

## URLField

Corresponds to `django.db.models.fields.URLField`. Uses Django's `django.core.validators.URLValidator` for validation.

**Signature:** `CharField(max_length=200, min_length=None)`

## SlugField

Corresponds to `django.db.models.fields.SlugField`.

**Signature:** `CharField(max_length=50, min_length=None)`

## ChoiceField

A field that can accept a value out of a limited set of choices.

## EmailField

A text representation, validates the text to be a valid e-mail address.

Corresponds to `django.db.models.fields.EmailField`

## RegexField

A text representation, that validates the given value matches against a certain regular expression.

Uses Django's `django.core.validators.RegexValidator` for validation.

Corresponds to `django.forms.fields.RegexField`

**Signature:** `RegexField(regex, max_length=None, min_length=None)`

## DateTimeField

A date and time representation.

Corresponds to `django.db.models.fields.DateTimeField`

When using `ModelSerializer` or `HyperlinkedModelSerializer`, note that any model fields with `auto_now=True` or `auto_now_add=True` will use serializer fields that are `read_only=True` by default.

If you want to override this behavior, you'll need to declare the `DateTimeField` explicitly on the serializer.  For example:

    class CommentSerializer(serializers.ModelSerializer):
        created = serializers.DateTimeField()

        class Meta:
            model = Comment

**Signature:** `DateTimeField(format=None, input_formats=None)`

* `format` - A string representing the output format.  If not specified, the `DATETIME_FORMAT` setting will be used, which defaults to `'iso-8601'`.
* `input_formats` - A list of strings representing the input formats which may be used to parse the date. If not specified, the `DATETIME_INPUT_FORMATS` setting will be used, which defaults to `['iso-8601']`.

DateTime format strings may either be [python strftime formats][strftime] which explicitly specifiy the format, or the special string `'iso-8601'`, which indicates that [ISO 8601][iso8601] style datetimes should be used. (eg `'2013-01-29T12:34:56.000000'`)

## DateField

A date representation.

Corresponds to `django.db.models.fields.DateField`

**Signature:** `DateField(format=None, input_formats=None)`

* `format` - A string representing the output format.  If not specified, the `DATE_FORMAT` setting will be used, which defaults to `'iso-8601'`.
* `input_formats` - A list of strings representing the input formats which may be used to parse the date. If not specified, the `DATE_INPUT_FORMATS` setting will be used, which defaults to `['iso-8601']`. 

Date format strings may either be [python strftime formats][strftime] which explicitly specifiy the format, or the special string `'iso-8601'`, which indicates that [ISO 8601][iso8601] style dates should be used. (eg `'2013-01-29'`)

## TimeField

A time representation.

Optionally takes `format` as parameter to replace the matching pattern.

Corresponds to `django.db.models.fields.TimeField`

**Signature:** `TimeField(format=None, input_formats=None)`

* `format` - A string representing the output format.  If not specified, the `TIME_FORMAT` setting will be used, which defaults to `'iso-8601'`.
* `input_formats` - A list of strings representing the input formats which may be used to parse the date. If not specified, the `TIME_INPUT_FORMATS` setting will be used, which defaults to `['iso-8601']`.

Time format strings may either be [python strftime formats][strftime] which explicitly specifiy the format, or the special string `'iso-8601'`, which indicates that [ISO 8601][iso8601] style times should be used. (eg `'12:34:56.000000'`)

## IntegerField

An integer representation.

Corresponds to `django.db.models.fields.IntegerField`, `django.db.models.fields.SmallIntegerField`, `django.db.models.fields.PositiveIntegerField` and `django.db.models.fields.PositiveSmallIntegerField`

## FloatField

A floating point representation.

Corresponds to `django.db.models.fields.FloatField`.

## FileField

A file representation. Performs Django's standard FileField validation. 

Corresponds to `django.forms.fields.FileField`.

**Signature:** `FileField(max_length=None, allow_empty_file=False)`

 - `max_length` designates the maximum length for the file name.
  
 - `allow_empty_file` designates if empty files are allowed.

## ImageField

An image representation.

Corresponds to `django.forms.fields.ImageField`.

Requires the `PIL` package.

Signature and validation is the same as with `FileField`.

---

**Note:** `FileFields` and `ImageFields` are only suitable for use with MultiPartParser, since e.g. json doesn't support file uploads.
Django's regular [FILE_UPLOAD_HANDLERS] are used for handling uploaded files.

---

[cite]: https://docs.djangoproject.com/en/dev/ref/forms/api/#django.forms.Form.cleaned_data
[FILE_UPLOAD_HANDLERS]: https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-FILE_UPLOAD_HANDLERS
[strftime]: http://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior
[iso8601]: http://www.w3.org/TR/NOTE-datetime
