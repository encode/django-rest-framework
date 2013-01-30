<a class="github" href="relations.py"></a>

# Serializer relations

> Bad programmers worry about the code.
> Good programmers worry about data structures and their relationships.
>
> &mdash; [Linus Torvalds][cite]


Relational fields are used to represent model relationships.  They can be applied to `ForeignKey`, `ManyToManyField` and `OneToOneField` relationships, as well as to reverse relationships, and custom relationships such as `GenericForeignKey`.

---

**Note:** The relational fields are declared in `relations.py`, but by convention you should import them using `from rest_framework import serializers` and refer to fields as `serializers.<FieldName>`.

---

## RelatedField

This field can be applied to any of the following:

* A `ForeignKey` field.
* A `OneToOneField` field.
* A reverse OneToOne relationship
* Any other "to-one" relationship.

By default `RelatedField` will represent the target of the field using it's `__unicode__` method.

You can customize this behavior by subclassing `ManyRelatedField`, and overriding the `.to_native(self, value)` method.

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
        tags = serializers.ManyRelatedField()

        class Meta:
            model = Bookmark
            exclude = ('id',)

Then an example output format for a Bookmark instance would be:

    {
        'tags': [u'django', u'python'],
        'url': u'https://www.djangoproject.com/'
    }

## PrimaryKeyRelatedField
## ManyPrimaryKeyRelatedField

`PrimaryKeyRelatedField` and `ManyPrimaryKeyRelatedField` will represent the target of the relationship using it's primary key.

By default these fields are read-write, although you can change this behavior using the `read_only` flag.

**Arguments**:

* `queryset` - By default `ModelSerializer` classes will use the default queryset for the relationship.  `Serializer` classes must either set a queryset explicitly, or set `read_only=True`.
* `null` - If set to `True`, the field will accept values of `None` or the empty-string for nullable relationships.

## SlugRelatedField
## ManySlugRelatedField

`SlugRelatedField` and `ManySlugRelatedField` will represent the target of the relationship using a unique slug.

By default these fields read-write, although you can change this behavior using the `read_only` flag.

**Arguments**:

* `slug_field` - The field on the target that should be used to represent it.  This should be a field that uniquely identifies any given instance.  For example, `username`.
* `queryset` - By default `ModelSerializer` classes will use the default queryset for the relationship.  `Serializer` classes must either set a queryset explicitly, or set `read_only=True`.
* `null` - If set to `True`, the field will accept values of `None` or the empty-string for nullable relationships.

## HyperlinkedRelatedField
## ManyHyperlinkedRelatedField

`HyperlinkedRelatedField` and `ManyHyperlinkedRelatedField` will represent the target of the relationship using a hyperlink.

By default, `HyperlinkedRelatedField` is read-write, although you can change this behavior using the `read_only` flag.

**Arguments**:

* `view_name` - The view name that should be used as the target of the relationship.  **required**.
* `format` - If using format suffixes, hyperlinked fields will use the same format suffix for the target unless overridden by using the `format` argument.
* `queryset` - By default `ModelSerializer` classes will use the default queryset for the relationship.  `Serializer` classes must either set a queryset explicitly, or set `read_only=True`.
* `slug_field` - The field on the target that should be used for the lookup. Default is `'slug'`.
* `pk_url_kwarg` - The named url parameter for the pk field lookup. Default is `pk`.
* `slug_url_kwarg` - The named url parameter for the slug field lookup. Default is to use the same value as given for `slug_field`.
* `null` - If set to `True`, the field will accept values of `None` or the empty-string for nullable relationships.

## HyperLinkedIdentityField

This field can be applied as an identity relationship, such as the `'url'` field on  a HyperlinkedModelSerializer.

This field is always read-only.

**Arguments**:

* `view_name` - The view name that should be used as the target of the relationship.  **required**.
* `format` - If using format suffixes, hyperlinked fields will use the same format suffix for the target unless overridden by using the `format` argument.
* `slug_field` - The field on the target that should be used for the lookup. Default is `'slug'`.
* `pk_url_kwarg` - The named url parameter for the pk field lookup. Default is `pk`.
* `slug_url_kwarg` - The named url parameter for the slug field lookup. Default is to use the same value as given for `slug_field`.

[cite]: http://lwn.net/Articles/193245/
