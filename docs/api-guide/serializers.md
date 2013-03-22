<a class="github" href="serializers.py"></a>

# Serializers

> Expanding the usefulness of the serializers is something that we would
like to address. However, it's not a trivial problem, and it
will take some serious design work.
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
            """
            Given a dictionary of deserialized field values, either update
            an existing model instance, or create a new model instance.
            """
            if instance is not None:
                instance.title = attrs.get('title', instance.title)
                instance.content = attrs.get('content', instance.content)
                instance.created = attrs.get('created', instance.created)
                return instance
            return Comment(**attrs) 

The first part of serializer class defines the fields that get serialized/deserialized.  The `restore_object` method defines how fully fledged instances get created when deserializing data.

The `restore_object` method is optional, and is only required if we want our serializer to support deserialization into fully fledged object instances.  If we don't define this method, then deserializing data will simply return a dictionary of items.

## Serializing objects

We can now use `CommentSerializer` to serialize a comment, or list of comments.  Again, using the `Serializer` class looks a lot like using a `Form` class.

    serializer = CommentSerializer(comment)
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

    serializer = CommentSerializer(data=data)
    serializer.is_valid()
    # True
    serializer.object
    # <Comment object at 0x10633b2d0>
    >>> serializer.deserialize('json', stream)

When deserializing data, we can either create a new instance, or update an existing instance.

    serializer = CommentSerializer(data=data)           # Create new instance
    serializer = CommentSerializer(comment, data=data)  # Update `instance`

By default, serializers must be passed values for all required fields or they will throw validation errors.  You can use the `partial` argument in order to allow partial updates.

    serializer = CommentSerializer(comment, data={'content': u'foo bar'}, partial=True)  # Update `instance` with partial data

## Validation

When deserializing data, you always need to call `is_valid()` before attempting to access the deserialized object.  If any validation errors occur, the `.errors` property will contain a dictionary representing the resulting error messages.  For example:

    serializer = CommentSerializer(data={'email': 'foobar', 'content': 'baz'})
    serializer.is_valid()
    # False
    serializer.errors
    # {'email': [u'Enter a valid e-mail address.'], 'created': [u'This field is required.']}

Each key in the dictionary will be the field name, and the values will be lists of strings of any error messages corresponding to that field.  The `non_field_errors` key may also be present, and will list any general validation errors.

When deserializing a list of items, errors will be returned as a list of dictionaries representing each of the deserialized items.

#### Field-level validation

You can specify custom field-level validation by adding `.validate_<fieldname>` methods to your `Serializer` subclass. These are analagous to `.clean_<fieldname>` methods on Django forms, but accept slightly different arguments.

They take a dictionary of deserialized attributes as a first argument, and the field name in that dictionary as a second argument (which will be either the name of the field or the value of the `source` argument to the field, if one was provided).

Your `validate_<fieldname>` methods should either just return the `attrs` dictionary or raise a `ValidationError`. For example:

    from rest_framework import serializers

    class BlogPostSerializer(serializers.Serializer):
        title = serializers.CharField(max_length=100)
        content = serializers.CharField()

        def validate_title(self, attrs, source):
            """
            Check that the blog post is about Django.
            """
            value = attrs[source]
            if "django" not in value.lower():
                raise serializers.ValidationError("Blog post is not about Django")
            return attrs

#### Object-level validation

To do any other validation that requires access to multiple fields, add a method called `.validate()` to your `Serializer` subclass. This method takes a single argument, which is the `attrs` dictionary. It should raise a `ValidationError` if necessary, or just return `attrs`.  For example:

    from rest_framework import serializers

    class EventSerializer(serializers.Serializer):
        description = serializers.CharField(max_length=100)
        start = serializers.DateTimeField()
        finish = serializers.DateTimeField()

        def validate(self, attrs):
            """
            Check that the start is before the stop.
            """
            if attrs['start'] < attrs['finish']:
                raise serializers.ValidationError("finish must occur after start")
            return attrs

## Saving object state

To save the deserialized objects created by a serializer, call the `.save()` method:

    if serializer.is_valid():
        serializer.save()

The default behavior of the method is to simply call `.save()` on the deserialized object instance.  You can override the default save behaviour by overriding the `.save_object(obj)` method on the serializer class.

The generic views provided by REST framework call the `.save()` method when updating or creating entities.  

## Dealing with nested objects

The previous examples are fine for dealing with objects that only have simple datatypes, but sometimes we also need to be able to represent more complex objects, where some of the attributes of an object might not be simple datatypes such as strings, dates or integers.

The `Serializer` class is itself a type of `Field`, and can be used to represent relationships where one object type is nested inside another.

    class UserSerializer(serializers.Serializer):
        email = serializers.EmailField()
        username = serializers.CharField(max_length=100)

    class CommentSerializer(serializers.Serializer):
        user = UserSerializer()
        content = serializers.CharField(max_length=200)
        created = serializers.DateTimeField()

If a nested representation may optionally accept the `None` value you should pass the `required=False` flag to the nested serializer.

    class CommentSerializer(serializers.Serializer):
        user = UserSerializer(required=False)  # May be an anonymous user.
        content = serializers.CharField(max_length=200)
        created = serializers.DateTimeField()

Similarly if a nested representation should be a list of items, you should the `many=True` flag to the nested serialized.

    class CommentSerializer(serializers.Serializer):
        user = UserSerializer(required=False)
        edits = EditItemSerializer(many=True)  # A nested list of 'edit' items.
        content = serializers.CharField(max_length=200)
        created = serializers.DateTimeField()

---

**Note**: Nested serializers are only suitable for read-only representations, as there are cases where they would have ambiguous or non-obvious behavior if used when updating instances.  For read-write representations you should always use a flat representation, by using one of the `RelatedField` subclasses.

---

## Dealing with multiple objects

The `Serializer` class can also handle serializing or deserializing lists of objects.

#### Serializing multiple objects

To serialize a queryset or list of objects instead of a single object instance, you should pass the `many=True` flag when instantiating the serializer.  You can then pass a queryset or list of objects to be serialized.

    queryset = Book.objects.all()
    serializer = BookSerializer(queryset, many=True)
    serializer.data
    # [
    #     {'id': 0, 'title': 'The electric kool-aid acid test', 'author': 'Tom Wolfe'},
    #     {'id': 1, 'title': 'If this is a man', 'author': 'Primo Levi'},
    #     {'id': 2, 'title': 'The wind-up bird chronicle', 'author': 'Haruki Murakami'}
    # ]

#### Deserializing multiple objects for creation

To deserialize a list of object data, and create multiple object instances in a single pass, you should also set the `many=True` flag, and pass a list of data to be deserialized.

This allows you to write views that create multiple items when a `POST` request is made.

For example:

    data = [
        {'title': 'The bell jar', 'author': 'Sylvia Plath'},
        {'title': 'For whom the bell tolls', 'author': 'Ernest Hemingway'}
    ]
    serializer = BookSerializer(data=data, many=True)
    serializer.is_valid()
    # True
    serializer.save()  # `.save()` will be called on each deserialized instance

#### Deserializing multiple objects for update

You can also deserialize a list of objects as part of a bulk update of multiple existing items.
In this case you need to supply both an existing list or queryset of items, as well as a list of data to update those items with.

This allows you to write views that update or create multiple items when a `PUT` request is made.

    # Capitalizing the titles of the books
    queryset = Book.objects.all()
    data = [
        {'id': 3, 'title': 'The Bell Jar', 'author': 'Sylvia Plath'},
        {'id': 4, 'title': 'For Whom the Bell Tolls', 'author': 'Ernest Hemingway'}
    ]
    serializer = BookSerializer(queryset, data=data, many=True)
    serializer.is_valid()
    # True
    serialize.save()  # `.save()` will be called on each updated or newly created instance.

Bulk updates will update any instances that already exist, and create new instances for data items that do not have a corresponding instance.

When performing a bulk update you may want any items that are not present in the incoming data to be deleted.  To do so, pass `allow_delete=True` to the serializer.

    serializer = BookSerializer(queryset, data=data, many=True, allow_delete=True)
    serializer.is_valid()
    # True
    serializer.save()  # `.save()` will be called on each updated or newly created instance.
                       # `.delete()` will be called on any other items in the `queryset`.

Passing `allow_delete=True` ensures that any update operations will completely overwrite the existing queryset, rather than simply updating any objects found in the incoming data. 

#### How identity is determined when performing bulk updates

Performing a bulk update is slightly more complicated than performing a bulk creation, because the serializer needs a way of determining how the items in the incoming data should be matched against the existing object instances.

By default the serializer class will use the `id` key on the incoming data to determine the canonical identity of an object.  If you need to change this behavior you should override the `get_identity` method on the `Serializer` class.  For example:

    class AccountSerializer(serializers.Serializer):
        slug = serializers.CharField(max_length=100)
        created = serializers.DateTimeField()
        ...  # Various other fields
        
        def get_identity(self, data):
            """
            This hook is required for bulk update.
            We need to override the default, to use the slug as the identity.
            
            Note that the data has not yet been validated at this point,
            so we need to deal gracefully with incorrect datatypes.
            """
            try:
                return data.get('slug', None)
            except AttributeError:
                return None

To map the incoming data items to their corresponding object instances, the `.get_identity()` method will be called both against the incoming data, and against the serialized representation of the existing objects.

## Including extra context

There are some cases where you need to provide extra context to the serializer in addition to the object being serialized.  One common case is if you're using a serializer that includes hyperlinked relations, which requires the serializer to have access to the current request so that it can properly generate fully qualified URLs.

You can provide arbitrary additional context by passing a `context` argument when instantiating the serializer. For example:

    serializer = AccountSerializer(account, context={'request': request})
    serializer.data
    # {'id': 6, 'owner': u'denvercoder9', 'created': datetime.datetime(2013, 2, 12, 09, 44, 56, 678870), 'details': 'http://example.com/accounts/6/details'}

The context dictionary can be used within any serializer field logic, such as a custom `.to_native()` method, by accessing the `self.context` attribute.

---

# ModelSerializers

Often you'll want serializer classes that map closely to model definitions.
The `ModelSerializer` class lets you automatically create a Serializer class with fields that correspond to the Model fields.

    class AccountSerializer(serializers.ModelSerializer):
        class Meta:
            model = Account

By default, all the model fields on the class will be mapped to corresponding serializer fields.

Any foreign keys on the model will be mapped to `PrimaryKeyRelatedField` if you're using a `ModelSerializer`, or `HyperlinkedRelatedField` if you're using a `HyperlinkedModelSerializer`.

## Specifying fields explicitly 

You can add extra fields to a `ModelSerializer` or override the default fields by declaring fields on the class, just as you would for a `Serializer` class.

    class AccountSerializer(serializers.ModelSerializer):
        url = serializers.CharField(source='get_absolute_url', read_only=True)
        groups = serializers.PrimaryKeyRelatedField(many=True)

        class Meta:
            model = Account

Extra fields can correspond to any property or callable on the model.

## Relational fields

When serializing model instances, there are a number of different ways you might choose to represent relationships.  The default representation for `ModelSerializer` is to use the primary keys of the related instances.

Alternative representations include serializing using hyperlinks, serializing complete nested representations, or serializing with a custom representation.

For full details see the [serializer relations][relations] documentation.

## Specifying which fields should be included

If you only want a subset of the default fields to be used in a model serializer, you can do so using `fields` or `exclude` options, just as you would with a `ModelForm`.

For example:

    class AccountSerializer(serializers.ModelSerializer):
        class Meta:
            model = Account
            exclude = ('id',)

## Specifiying nested serialization

The default `ModelSerializer` uses primary keys for relationships, but you can also easily generate nested representations using the `depth` option:

    class AccountSerializer(serializers.ModelSerializer):
        class Meta:
            model = Account
            exclude = ('id',)
            depth = 1

The `depth` option should be set to an integer value that indicates the depth of relationships that should be traversed before reverting to a flat representation.

## Specifying which fields should be read-only 

You may wish to specify multiple fields as read-only. Instead of adding each field explicitely with the `read_only=True` attribute, you may use the `read_only_fields` Meta option, like so:

    class AccountSerializer(serializers.ModelSerializer):
        class Meta:
            model = Account
            read_only_fields = ('created', 'modified')

## Customising the default fields

You can create customized subclasses of `ModelSerializer` that use a different set of default fields for the representation, by overriding various `get_<field_type>_field` methods.

Each of these methods may either return a field or serializer instance, or `None`.

### get_pk_field

**Signature**: `.get_pk_field(self, model_field)`

Returns the field instance that should be used to represent the pk field.

### get_nested_field

**Signature**: `.get_nested_field(self, model_field)`

Returns the field instance that should be used to represent a related field when `depth` is specified as being non-zero.

### get_related_field

**Signature**: `.get_related_field(self, model_field, to_many=False)`

Returns the field instance that should be used to represent a related field when `depth` is not specified, or when nested representations are being used and the depth reaches zero.

### get_field

**Signature**: `.get_field(self, model_field)`

Returns the field instance that should be used for non-relational, non-pk fields.

### Example:

The following custom model serializer could be used as a base class for model serializers that should always exclude the pk by default.

    class NoPKModelSerializer(serializers.ModelSerializer):
        def get_pk_field(self, model_field):
            return None



[cite]: https://groups.google.com/d/topic/django-users/sVFaOfQi4wY/discussion
[relations]: relations.md
