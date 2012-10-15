<a class="github" href="fields.py"></a>

# Serializer fields

> Flat is better than nested.
>
> &mdash; [The Zen of Python][cite]

Serializer fields handle converting between primative values and internal datatypes.  They also deal with validating input values, as well as retrieving and setting the values from their parent objects.

---

**Note:** The serializer fields are declared in fields.py, but by convention you should import them using `from rest_framework import serializers` and refer to fields as `serializers.<FieldName>`.

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

Would produced output similar to:

    {
        'url': 'http://example.com/api/accounts/3/',
        'owner': 'http://example.com/api/users/12/',
        'name': 'FooCorp business account', 
        'expired': True
    }

Be default, the `Field` class will perform a basic translation of the source value into primative datatypes, falling back to unicode representations of complex datatypes when neccesary.

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

A Boolean representation, corresponds to `django.db.models.fields.BooleanField`.

## CharField

A text representation, optionally validates the text to be shorter than `max_length` and longer than `min_length`, corresponds to `django.db.models.fields.CharField`
or `django.db.models.fields.TextField`.

**Signature:** `CharField([max_length=<Integer>[, min_length=<Integer>]])`

## EmailField

A text representation, validates the text to be a valid e-mail adress. Corresponds to `django.db.models.fields.EmailField`

## DateField

A date representation. Corresponds to `django.db.models.fields.DateField`

## DateTimeField

A date and time representation. Corresponds to `django.db.models.fields.DateTimeField`

## IntegerField

An integer representation. Corresponds to `django.db.models.fields.IntegerField`, `django.db.models.fields.SmallIntegerField`, `django.db.models.fields.PositiveIntegerField` and `django.db.models.fields.PositiveSmallIntegerField`

## FloatField

A floating point representation. Corresponds to `django.db.models.fields.FloatField`.

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

The an example output format for a Bookmark instance would be:

    {
        'tags': [u'django', u'python'],
        'url': u'https://www.djangoproject.com/'
    }

## PrimaryKeyRelatedField

As with `RelatedField` field can be applied to any "to-one" relationship, such as a `ForeignKey` field.

`PrimaryKeyRelatedField` will represent the target of the field using it's primary key.

Be default, `PrimaryKeyRelatedField` is read-write, although you can change this behaviour using the `readonly` flag.

## ManyPrimaryKeyRelatedField

As with `RelatedField` field can be applied to any "to-many" relationship, such as a `ManyToManyField` field, or a reverse `ForeignKey` relationship.

`PrimaryKeyRelatedField` will represent the target of the field using their primary key.

Be default, `ManyPrimaryKeyRelatedField` is read-write, although you can change this behaviour using the `readonly` flag.

## HyperlinkedRelatedField

## ManyHyperlinkedRelatedField

## HyperLinkedIdentityField

[cite]: http://www.python.org/dev/peps/pep-0020/
