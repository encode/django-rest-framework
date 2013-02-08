<a class="github" href="relations.py"></a>

# Serializer relations

> Bad programmers worry about the code.
> Good programmers worry about data structures and their relationships.
>
> &mdash; [Linus Torvalds][cite]


Relational fields are used to represent model relationships.  They can be applied to `ForeignKey`, `ManyToManyField` and `OneToOneField` relationships, as well as to reverse relationships, and custom relationships such as `GenericForeignKey`.

---

**Note:** The relational fields are declared in `relations.py`, but by convention you should import them from the `serializers` module, using `from rest_framework import serializers` and refer to fields as `serializers.<FieldName>`.

---

# API Reference

In order to explain the various types of relational fields, we'll use a couple of simple models for our examples.  Our models will be for music albums, and the tracks listed on each album.

    class Album(models.Model):
        album_name = models.CharField(max_length=100)
        artist = models.CharField(max_length=100)

    class Track(models.Model):
        album = models.ForeignKey(Album, related_name='tracks')
        order = models.IntegerField()
        title = models.CharField(max_length=100)
        duration = models.IntegerField()

        class Meta:
            unique_together = ('album', 'order')
        
        def __unicode__(self):
            return '%d: %s' % (self.order, self.title)

## RelatedField

`RelatedField` may be used to represent the target of the relationship using it's `__unicode__` method.

For example, the following serializer.
 
    class AlbumSerializer(serializer.ModelSerializer):
        tracks = RelatedField(many=True)
        
        class Meta:
            model = Album
            fields = ('album_name', 'artist', 'tracks')

Would serialize to the following representation.

    {
        'album_name': 'Things We Lost In The Fire',
        'artist': 'Low'
        'tracks': [
            '1: Sunflower',
            '2: Whitetail',
            '3: Dinosaur Act',
            ...
        ]
    }

This field is read only.

## PrimaryKeyRelatedField

`PrimaryKeyRelatedField` may be used to represent the target of the relationship using it's primary key.

For example, the following serializer:
 
    class AlbumSerializer(serializer.ModelSerializer):
        tracks = PrimaryKeyRelatedField(many=True, read_only=True)
        
        class Meta:
            model = Album
            fields = ('album_name', 'artist', 'tracks')

Would serialize to a representation like this:

    {
        'album_name': 'The Roots',
        'artist': 'Undun'
        'tracks': [
            89,
            90,
            91,
            ...
        ]
    }

By default this field is read-write, although you can change this behavior using the `read_only` flag.

**Arguments**:

* `queryset` - By default `ModelSerializer` classes will use the default queryset for the relationship.  `Serializer` classes must either set a queryset explicitly, or set `read_only=True`.
* `required` - If set to `False`, the field will accept values of `None` or the empty-string for nullable relationships.

## HyperlinkedRelatedField

`HyperlinkedRelatedField` may be used to represent the target of the relationship using a hyperlink.

For example, the following serializer:
 
    class AlbumSerializer(serializer.ModelSerializer):
        tracks = HyperlinkedRelatedField(many=True, read_only=True,
                                         view_name='track-detail')
        
        class Meta:
            model = Album
            fields = ('album_name', 'artist', 'tracks')

Would serialize to a representation like this:

    {
        'album_name': 'Graceland',
        'artist': 'Paul Simon'
        'tracks': [
            'http://www.example.com/api/tracks/45',
            'http://www.example.com/api/tracks/46',
            'http://www.example.com/api/tracks/47',
            ...
        ]
    }

By default this field is read-write, although you can change this behavior using the `read_only` flag.

**Arguments**:

* `view_name` - The view name that should be used as the target of the relationship.  **required**.
* `required` - If set to `False`, the field will accept values of `None` or the empty-string for nullable relationships.
* `queryset` - By default `ModelSerializer` classes will use the default queryset for the relationship.  `Serializer` classes must either set a queryset explicitly, or set `read_only=True`.
* `slug_field` - The field on the target that should be used for the lookup. Default is `'slug'`.
* `pk_url_kwarg` - The named url parameter for the pk field lookup. Default is `pk`.
* `slug_url_kwarg` - The named url parameter for the slug field lookup. Default is to use the same value as given for `slug_field`.
* `format` - If using format suffixes, hyperlinked fields will use the same format suffix for the target unless overridden by using the `format` argument.

## SlugRelatedField

`SlugRelatedField` may be used to represent the target of the relationship using a field on the target.

For example, the following serializer:
 
    class AlbumSerializer(serializer.ModelSerializer):
        tracks = SlugRelatedField(many=True, read_only=True, slug_field='title')
        
        class Meta:
            model = Album
            fields = ('album_name', 'artist', 'tracks')

Would serialize to a representation like this:

    {
        'album_name': 'Dear John',
        'artist': 'Loney Dear'
        'tracks': [
            'Airport Surroundings',
            'Everything Turns to You',
            'I Was Only Going Out',
            ...
        ]
    }

By default this field is read-write, although you can change this behavior using the `read_only` flag.

When using `SlugRelatedField` as a read-write field, you will normally want to ensure that the slug field corresponds to a model field with `unique=True`.

**Arguments**:

* `slug_field` - The field on the target that should be used to represent it.  This should be a field that uniquely identifies any given instance.  For example, `username`.
* `queryset` - By default `ModelSerializer` classes will use the default queryset for the relationship.  `Serializer` classes must either set a queryset explicitly, or set `read_only=True`.
* `null` - If set to `True`, the field will accept values of `None` or the empty-string for nullable relationships.

## HyperLinkedIdentityField

This field can be applied as an identity relationship, such as the `'url'` field on  a HyperlinkedModelSerializer.  It can also be used for an attribute on the object.  For example, the following serializer:

    class AlbumSerializer(serializers.HyperlinkedModelSerializer):
        track_listing = HyperLinkedIdentityField(view_name='track-list')

        class Meta:
            model = Album
            fields = ('album_name', 'artist', 'track_listing')

Would serialize to a representation like this:

    {
        'album_name': 'The Eraser',
        'artist': 'Thom Yorke'
        'track_listing': 'http://www.example.com/api/track_list/12',
    }
 
This field is always read-only.

**Arguments**:

* `view_name` - The view name that should be used as the target of the relationship.  **required**.
* `slug_field` - The field on the target that should be used for the lookup. Default is `'slug'`.
* `pk_url_kwarg` - The named url parameter for the pk field lookup. Default is `pk`.
* `slug_url_kwarg` - The named url parameter for the slug field lookup. Default is to use the same value as given for `slug_field`.
* `format` - If using format suffixes, hyperlinked fields will use the same format suffix for the target unless overridden by using the `format` argument.

## Nested relationships

Nested relationships can be expressed by using serializers as fields.  For example:

    class TrackSerializer(serializer.ModelSerializer):
        class Meta:
            fields = ('order', 'title')
    
    class AlbumSerializer(serializer.ModelSerializer):
        tracks = TrackSerializer(many=True)
        
        class Meta:
            model = Album
            fields = ('album_name', 'artist', 'tracks')

Note that nested relationships are currently read-only.  For read-write relationships, you should use a flat relational style.

## Custom relational fields

To implement a custom relational field, you should override `RelatedField`, and implement the `.to_native(self, value)` method.  This method takes the target of the field as the `value` argument, and should return the representation that should be used to serialize the target.

    class TrackListingField(serializers.RelatedField):
        def to_native(self, value):
            return 'Track %d: %s' % (value.ordering, value.name)

If you want to implement a read-write relational field, you must also implement the `.from_native(self, data)` method, and add `read_only = False` to the class definition.

# Further notes

## Reverse relations

Note that reverse relationships are not automatically generated by the `ModelSerializer` and `HyperlinkedModelSerializer` classes.  To include a reverse relationship, you cannot simply add it to the fields list.

**The following will not work:**

    class AlbumSerializer(serializer.ModelSerializer):
        class Meta:
            fields = ('tracks', ...) 
           
Instead, you must explicitly add it to the serializer.  For example:

    class AlbumSerializer(serializer.ModelSerializer):
        tracks = serializers.PrimaryKeyRelationship(many=True)
        ...

By default, the field will uses the same accessor as it's field name to retrieve the relationship, so in this example, `Album` instances would need to have the `tracks` attribute for this relationship to work.

The best way to ensure this is typically to make sure that the relationship on the model definition has it's `related_name` argument properly set.  For example:

    class Track(models.Model):
        album = models.ForeignKey(Album, related_name='tracks')
        ...

Alternatively, you can use the `source` argument on the serializer field, to use a different accessor attribute than the field name.  For example.

    class AlbumSerializer(serializer.ModelSerializer):
        tracks = serializers.PrimaryKeyRelationship(many=True, source='track_set')

See the Django documentation on [reverse relationships][reverse-relationships] for more details.

## Generic relationships

If you want to serialize a generic foreign key, you need to define a custom field, to determine explicitly how you want serialize the targets of the relationship.

For example, given the following model for a tag, which has a generic relationship with other arbitrary models:

    class TaggedItem(models.Model):
        """
        Tags arbitrary model instances using a generic relation.
        
        See: https://docs.djangoproject.com/en/dev/ref/contrib/contenttypes/
        """
        tag_name = models.SlugField()
        content_type = models.ForeignKey(ContentType)
        object_id = models.PositiveIntegerField()
        tagged_object = GenericForeignKey('content_type', 'object_id')
    
        def __unicode__(self):
            return self.tag

And the following two models, which may be have associated tags:

    class Bookmark(models.Model):
        """
        A bookmark consists of a URL, and 0 or more descriptive tags.
        """
        url = models.URLField()
        tags = GenericRelation(TaggedItem)


    class Note(models.Model):
        """
        A note consists of some text, and 0 or more descriptive tags.
        """
        text = models.CharField(max_length=1000)
        tags = GenericRelation(TaggedItem)

We could define a custom field that could be used to serialize tagged instances, using the type of each instance to determine how it should be serialized.

    class TaggedObjectRelatedField(serializers.RelatedField):
        """
        A custom field to use for the `tagged_object` generic relationship.
        """

        def to_native(self, value):
            """
            Serialize tagged objects to a simple textual representation.
            """                            
            if isinstance(value, Bookmark):
                return 'Bookmark: ' + value.url
            elif isinstance(value, Note):
                return 'Note: ' + value.text
            raise Exception('Unexpected type of tagged object')

If you need the target of the relationship to have a nested representation, you can  use the required serializers inside the `.to_native()` method:

        def to_native(self, value):
            """
            Serialize bookmark instances using a bookmark serializer,
            and note instances using a note serializer.
            """                            
            if isinstance(value, Bookmark):
                serializer = BookmarkSerializer(value)
            elif isinstance(value, Note):
                serializer = NoteSerializer(value)
            else:
                raise Exception('Unexpected type of tagged object')

            return serializer.data

Note that reverse generic keys, expressed using the `GenericRelation` field, can be serialized using the regular relational field types, since the type of the target in the relationship is always known.

For more information see [the Django documentation on generic relations][generic-relations].

---

## Deprecated relational fields

The following classes have been deprecated, in favor of the `many=<bool>` syntax.
They continue to function, but their usage will raise a `PendingDeprecationWarning`, which is silent by default.
In the 2.3 release, this warning will be escalated to a `DeprecationWarning`.
In the 2.4 release, they will be removed entirely.

* `ManyRelatedField`
* `ManyPrimaryKeyRelatedField`
* `ManyHyperlinkedRelatedField`
* `ManySlugRelatedField`

[cite]: http://lwn.net/Articles/193245/
[reverse-relationships]: https://docs.djangoproject.com/en/dev/topics/db/queries/#following-relationships-backward
[generic-relations]: https://docs.djangoproject.com/en/dev/ref/contrib/contenttypes/#id1
