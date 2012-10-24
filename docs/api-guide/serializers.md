<a class="github" href="serializers.py"></a>

# Serializers

> Expanding the usefulness of the serializers is something that we would
like to address. However, it's not a trivial problem, and it
will take some serious design work. Any offers to help out in this
area would be gratefully accepted.
>
> &mdash; Russell Keith-Magee, [Django users group][cite]

Serializers allow complex data such as querysets and model instances to be converted to native python datatypes that can then be easily rendered into `JSON`, `XML` or other content types.  Serializers also provide deserialization, allowing parsed data to be converted back into complex types, after first validating the incoming data.

REST framework's serializers work very similarly to Django's `Form` and `ModelForm` classes.  It provides a `Serializer` class which gives you a powerful, generic way to control the output of your responses, as well as a `ModelSerializer` class which provides a useful shortcut for creating serializers that deal with model instances and querysets.

## Declaring Serializers

Let's start by creating a simple object we can use for example purposes:

    class Comment(object):
        def __init__(self, email, content, created=None):
            self.email = email
            self.content = content
            self.created = created or datetime.datetime.now()
    
    comment = Comment(email='leila@example.com', content='foo bar')

We'll declare a serializer that we can use to serialize and deserialize `Comment` objects.
Declaring a serializer looks very similar to declaring a form:

    class CommentSerializer(serializers.Serializer):
        email = serializers.EmailField()
        content = serializers.CharField(max_length=200)
        created = serializers.DateTimeField()

        def restore_object(self, attrs, instance=None):
            if instance:
                instance.title = attrs['title']
                instance.content = attrs['content']
                instance.created = attrs['created']
                return instance
            return Comment(**attrs) 

The first part of serializer class defines the fields that get serialized/deserialized.  The `restore_object` method defines how fully fledged instances get created when deserializing data.  The `restore_object` method is optional, and is only required if we want our serializer to support deserialization.

## Serializing objects

We can now use `CommentSerializer` to serialize a comment, or list of comments.  Again, using the `Serializer` class looks a lot like using a `Form` class.

    serializer = CommentSerializer(instance=comment)
    serializer.data
    # {'email': u'leila@example.com', 'content': u'foo bar', 'created': datetime.datetime(2012, 8, 22, 16, 20, 9, 822774)}

At this point we've translated the model instance into python native datatypes.  To finalise the serialization process we render the data into `json`.

    stream = JSONRenderer().render(data)
    stream
    # '{"email": "leila@example.com", "content": "foo bar", "created": "2012-08-22T16:20:09.822"}'

## Deserializing objects
        
Deserialization is similar.  First we parse a stream into python native datatypes... 

    data = JSONParser().parse(stream)

...then we restore those native datatypes into a fully populated object instance.

    serializer = CommentSerializer(data)
    serializer.is_valid()
    # True
    serializer.object
    # <Comment object at 0x10633b2d0>
    >>> serializer.deserialize('json', stream)

## Validation

When deserializing data, you always need to call `is_valid()` before attempting to access the deserialized object.  If any validation errors occur, the `.errors` and `.non_field_errors` properties will contain the resulting error messages.

### Field-level validation

You can specify custom field-level validation by adding `validate_<fieldname>()` methods to your `Serializer` subclass. These are analagous to `clean_<fieldname>` methods on Django forms, but accept slightly different arguments. They take a dictionary of deserialized attributes as a first argument, and the field name in that dictionary as a second argument (which will be either the name of the field or the value of the `source` argument to the field, if one was provided). Your `validate_<fieldname>` methods should either just return the attrs dictionary or raise a `ValidationError`. For example:

    from rest_framework import serializers

    class BlogPostSerializer(serializers.Serializer):
        title = serializers.CharField(max_length=100)
        content = serializers.CharField()

        def validate_title(self, attrs, source):
            """
            Check that the blog post is about Django
            """
            value = attrs[source]
            if "Django" not in value:
                raise serializers.ValidationError("Blog post is not about Django")
            return attrs

### Final cross-field validation

To do any other validation that requires access to multiple fields, add a method called `validate` to your `Serializer` subclass. This method takes a single argument, which is the `attrs` dictionary. It should raise a `ValidationError` if necessary, or just return `attrs`.

## Dealing with nested objects

The previous example is fine for dealing with objects that only have simple datatypes, but sometimes we also need to be able to represent more complex objects,
where some of the attributes of an object might not be simple datatypes such as strings, dates or integers.

The `Serializer` class is itself a type of `Field`, and can be used to represent relationships where one object type is nested inside another.

    class UserSerializer(serializers.Serializer):
        email = serializers.EmailField()
        username = serializers.CharField()
        
        def restore_object(self, attrs, instance=None):
            return User(**attrs)


    class CommentSerializer(serializers.Serializer):
        user = UserSerializer()
        title = serializers.CharField()
        content = serializers.CharField(max_length=200)
        created = serializers.DateTimeField()
        
        def restore_object(self, attrs, instance=None):
            return Comment(**attrs)

## Creating custom fields

If you want to create a custom field, you'll probably want to override either one or both of the `.to_native()` and `.from_native()` methods.  These two methods are used to convert between the intial datatype, and a primative, serializable datatype.  Primative datatypes may be any of a number, string, date/time/datetime or None.  They may also be any list or dictionary like object that only contains other primative objects.

The `.to_native()` method is called to convert the initial datatype into a primative, serializable datatype.  The `from_native()` method is called to restore a primative datatype into it's initial representation.

Let's look at an example of serializing a class that represents an RGB color value:

    class Color(object):
        """
        A color represented in the RGB colorspace.
        """

        def __init__(self, red, green, blue):
            assert(red >= 0 and green >= 0 and blue >= 0)
            assert(red < 256 and green < 256 and blue < 256)
            self.red, self.green, self.blue = red, green, blue

    class ColourField(serializers.WritableField):
        """
        Color objects are serialized into "rgb(#, #, #)" notation.
        """

        def to_native(self, obj):
            return "rgb(%d, %d, %d)" % (obj.red, obj.green, obj.blue)
      
        def from_native(self, data):
            data = data.strip('rgb(').rstrip(')')
            red, green, blue = [int(col) for col in data.split(',')]
            return Color(red, green, blue)
            

By default field values are treated as mapping to an attribute on the object.  If you need to customize how the field value is accessed and set you need to override `.field_to_native()` and/or `.field_from_native()`.

As an example, let's create a field that can be used represent the class name of the object being serialized:

    class ClassNameField(serializers.WritableField):
        def field_to_native(self, obj, field_name):
            """
            Serialize the object's class name, not an attribute of the object.
            """
            return obj.__class__.__name__

        def field_from_native(self, data, field_name, into):
            """
            We don't want to set anything when we revert this field.
            """
            pass

---

# ModelSerializers

Often you'll want serializer classes that map closely to model definitions.
The `ModelSerializer` class lets you automatically create a Serializer class with fields that corrospond to the Model fields.

    class AccountSerializer(serializers.ModelSerializer):
        class Meta:
            model = Account

**[TODO: Explain model field to serializer field mapping in more detail]**

## Specifying fields explicitly 

You can add extra fields to a `ModelSerializer` or override the default fields by declaring fields on the class, just as you would for a `Serializer` class.

    class AccountSerializer(serializers.ModelSerializer):
        url = CharField(source='get_absolute_url', readonly=True)
        group = NaturalKeyField()

        class Meta:
            model = Account

Extra fields can correspond to any property or callable on the model.

## Relational fields

When serializing model instances, there are a number of different ways you might choose to represent relationships.  The default representation is to use the primary keys of the related instances.

Alternative representations include serializing using natural keys, serializing complete nested representations, or serializing using a custom representation, such as a URL that uniquely identifies the model instances.

The `PrimaryKeyRelatedField` and `HyperlinkedRelatedField` fields provide alternative flat representations.

The `ModelSerializer` class can itself be used as a field, in order to serialize relationships using nested representations.

The `RelatedField` class may be subclassed to create a custom representation of a relationship.  The subclass should override `.to_native()`, and optionally `.from_native()` if deserialization is supported.

All the relational fields may be used for any relationship or reverse relationship on a model.

## Specifying which fields should be included

If you only want a subset of the default fields to be used in a model serializer, you can do so using `fields` or `exclude` options, just as you would with a `ModelForm`.

For example:

    class AccountSerializer(serializers.ModelSerializer):
        class Meta:
            model = Account
            exclude = ('id',)

## Specifiying nested serialization

The default `ModelSerializer` uses primary keys for relationships, but you can also easily generate nested representations using the `nested` option:

    class AccountSerializer(serializers.ModelSerializer):
        class Meta:
            model = Account
            exclude = ('id',)
            nested = True

The `nested` option may be set to either `True`, `False`, or an integer value.  If given an integer value it indicates the depth of relationships that should be traversed before reverting to a flat representation.

When serializing objects using a nested representation any occurances of recursion will be recognised, and will fall back to using a flat representation.

## Customising the default fields used by a ModelSerializer



    class AccountSerializer(serializers.ModelSerializer):
        class Meta:
            model = Account

        def get_pk_field(self, model_field):
            return serializers.Field(readonly=True)

        def get_nested_field(self, model_field):
            return serializers.ModelSerializer()

        def get_related_field(self, model_field, to_many=False):
            queryset = model_field.rel.to._default_manager
            if to_many:
                return serializers.ManyRelatedField(queryset=queryset)
            return serializers.RelatedField(queryset=queryset)

        def get_field(self, model_field):
            return serializers.ModelField(model_field=model_field)


[cite]: https://groups.google.com/d/topic/django-users/sVFaOfQi4wY/discussion
