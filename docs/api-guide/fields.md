<a class="github" href="fields.py"></a>

# Serializer fields

> Flat is better than nested.
>
> &mdash; [The Zen of Python][cite]

Serializer fields handle converting between primative values and internal datatypes.  They also deal with validating input values, as well as retrieving and setting the values from their parent objects.

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

Set this to `True` to ensure that the field is used when serializing a representation, but is not used when updating an instance dureing deserialization.

Defaults to `False`

### `required`

Normally an error will be raised if a field is not supplied during deserialization.
Set to false if this field is not required to be present during deserialization.

Defaults to `True`.

### `default`

If set, this gives the default value that will be used for the field if none is supplied.  If not set the default behaviour is to not populate the attribute at all.

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

By default, the `Field` class will perform a basic translation of the source value into primative datatypes, falling back to unicode representations of complex datatypes when necessary.

You can customize this  behaviour by overriding the `.to_native(self, value)` method.

## WritableField

A field that supports both read and write operations.  By itself `WriteableField` does not perform any translation of input values into a given type.  You won't typically use this field directly, but you may want to override it and implement the `.to_native(self, value)` and `.from_native(self, value)` methods.

## ModelField

A generic field that can be tied to any arbitrary model field.  The `ModelField` class delegates the task of serialization/deserialization to it's associated model field.  This field can be used to create serializer fields for custom model fields, without having to create a new custom serializer field.

**Signature:** `ModelField(model_field=<Django ModelField class>)`

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

## DateField

A date representation.

Corresponds to `django.db.models.fields.DateField`

## DateTimeField

A date and time representation.

Corresponds to `django.db.models.fields.DateTimeField`

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

**Note:** `FileFields` and `ImageFields` are only suitable for use with MultiPartParser, since eg json doesn't support file uploads.
Django's regular [FILE_UPLOAD_HANDLERS] are used for handling uploaded files. 

---

# Relational Fields

Relational fields are used to represent model relationships.  They can be applied to `ForeignKey`, `ManyToManyField` and `OneToOneField` relationships, as well as to reverse relationships, and custom relationships such as `GenericForeignKey`.

## RelatedField

This field can be applied to any of the following:

* A `ForeignKey` field.
* A `OneToOneField` field.
* A reverse OneToOne relationship
* Any other "to-one" relationship.

By default `RelatedField` will represent the target of the field using it's `__unicode__` method.

You can customise this behaviour by subclassing `ManyRelatedField`, and overriding the `.to_native(self, value)` method.

## ManyRelatedField

This field can be applied to any of the following:
 
* A `ManyToManyField` field.
* A reverse ManyToMany relationship.
* A reverse ForeignKey relationship
* Any other "to-many" relationship.

By default `ManyRelatedField` will represent the targets of the field using their `__unicode__` method.

For example, given the following models:

    class TaggedItem(models.Model):
        """
        Tags arbitrary model instances using a generic relation.
        
        See: https://docs.djangoproject.com/en/dev/ref/contrib/contenttypes/
        """
        tag = models.SlugField()
        content_type = models.ForeignKey(ContentType)
        object_id = models.PositiveIntegerField()
        content_object = GenericForeignKey('content_type', 'object_id')
    
        def __unicode__(self):
            return self.tag
    
    
    class Bookmark(models.Model):
        """
        A bookmark consists of a URL, and 0 or more descriptive tags.
        """
        url = models.URLField()
        tags = GenericRelation(TaggedItem)

And a model serializer defined like this:

    class BookmarkSerializer(serializers.ModelSerializer):
        tags = serializers.ManyRelatedField(source='tags')

        class Meta:
            model = Bookmark
            exclude = ('id',)

Then an example output format for a Bookmark instance would be:

    {
        'tags': [u'django', u'python'],
        'url': u'https://www.djangoproject.com/'
    }

## PrimaryKeyRelatedField / ManyPrimaryKeyRelatedField

`PrimaryKeyRelatedField` and `ManyPrimaryKeyRelatedField` will represent the target of the relationship using it's primary key.

By default these fields are read-write, although you can change this behaviour using the `read_only` flag.

**Arguments**:

* `queryset` - By default `ModelSerializer` classes will use the default queryset for the relationship.  `Serializer` classes must either set a queryset explicitly, or set `read_only=True`.
* `null` - If set to `True`, the field will accept values of `None` or the emptystring for nullable relationships.

## SlugRelatedField / ManySlugRelatedField

`SlugRelatedField` and `ManySlugRelatedField` will represent the target of the relationship using a unique slug.

By default these fields read-write, although you can change this behaviour using the `read_only` flag.

**Arguments**:

* `slug_field` - The field on the target that should be used to represent it.  This should be a field that uniquely identifies any given instance.  For example, `username`.
* `queryset` - By default `ModelSerializer` classes will use the default queryset for the relationship.  `Serializer` classes must either set a queryset explicitly, or set `read_only=True`.
* `null` - If set to `True`, the field will accept values of `None` or the emptystring for nullable relationships.

## HyperlinkedRelatedField / ManyHyperlinkedRelatedField

`HyperlinkedRelatedField` and `ManyHyperlinkedRelatedField` will represent the target of the relationship using a hyperlink.

By default, `HyperlinkedRelatedField` is read-write, although you can change this behaviour using the `read_only` flag.

**Arguments**:

* `view_name` - The view name that should be used as the target of the relationship.  **required**.
* `format` - If using format suffixes, hyperlinked fields will use the same format suffix for the target unless overridden by using the `format` argument.
* `queryset` - By default `ModelSerializer` classes will use the default queryset for the relationship.  `Serializer` classes must either set a queryset explicitly, or set `read_only=True`.
* `slug_field` - The field on the target that should be used for the lookup. Default is `'slug'`.
* `pk_url_kwarg` - The named url parameter for the pk field lookup. Default is `pk`.
* `slug_url_kwarg` - The named url parameter for the slug field lookup. Default is to use the same value as given for `slug_field`.
* `null` - If set to `True`, the field will accept values of `None` or the emptystring for nullable relationships.

## HyperLinkedIdentityField

This field can be applied as an identity relationship, such as the `'url'` field on  a HyperlinkedModelSerializer.

This field is always read-only.

**Arguments**:

* `view_name` - The view name that should be used as the target of the relationship.  **required**.
* `format` - If using format suffixes, hyperlinked fields will use the same format suffix for the target unless overridden by using the `format` argument.
* `slug_field` - The field on the target that should be used for the lookup. Default is `'slug'`.
* `pk_url_kwarg` - The named url parameter for the pk field lookup. Default is `pk`.
* `slug_url_kwarg` - The named url parameter for the slug field lookup. Default is to use the same value as given for `slug_field`.

# Other Fields

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

[cite]: http://www.python.org/dev/peps/pep-0020/
[FILE_UPLOAD_HANDLERS]: https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-FILE_UPLOAD_HANDLERS
