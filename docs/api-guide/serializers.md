source: serializers.py

# Serializers

> Expanding the usefulness of the serializers is something that we would
like to address.  However, it's not a trivial problem, and it
will take some serious design work.
>
> &mdash; Russell Keith-Magee, [Django users group][cite]

Serializers allow complex data such as querysets and model instances to be converted to native Python datatypes that can then be easily rendered into `JSON`, `XML` or other content types.  Serializers also provide deserialization, allowing parsed data to be converted back into complex types, after first validating the incoming data.

The serializers in REST framework work very similarly to Django's `Form` and `ModelForm` classes. We provide a `Serializer` class which gives you a powerful, generic way to control the output of your responses, as well as a `ModelSerializer` class which provides a useful shortcut for creating serializers that deal with model instances and querysets.

## Declaring Serializers

Let's start by creating a simple object we can use for example purposes:

    class Comment(object):
        def __init__(self, email, content, created=None):
            self.email = email
            self.content = content
            self.created = created or datetime.datetime.now()

    comment = Comment(email='leila@example.com', content='foo bar')

We'll declare a serializer that we can use to serialize and deserialize data that corresponds to `Comment` objects.

Declaring a serializer looks very similar to declaring a form:

    from rest_framework import serializers

    class CommentSerializer(serializers.Serializer):
        email = serializers.EmailField()
        content = serializers.CharField(max_length=200)
        created = serializers.DateTimeField()

## Serializing objects

We can now use `CommentSerializer` to serialize a comment, or list of comments. Again, using the `Serializer` class looks a lot like using a `Form` class.

    serializer = CommentSerializer(comment)
    serializer.data
    # {'email': u'leila@example.com', 'content': u'foo bar', 'created': datetime.datetime(2012, 8, 22, 16, 20, 9, 822774)}

At this point we've translated the model instance into Python native datatypes.  To finalise the serialization process we render the data into `json`.

    from rest_framework.renderers import JSONRenderer

    json = JSONRenderer().render(serializer.data)
    json
    # '{"email": "leila@example.com", "content": "foo bar", "created": "2012-08-22T16:20:09.822"}'

## Deserializing objects

Deserialization is similar. First we parse a stream into Python native datatypes...

    from StringIO import StringIO
    from rest_framework.parsers import JSONParser

    stream = StringIO(json)
    data = JSONParser().parse(stream)

...then we restore those native datatypes into a dictionary of validated data.

    serializer = CommentSerializer(data=data)
    serializer.is_valid()
    # True
    serializer.validated_data
    # {'content': 'foo bar', 'email': 'leila@example.com', 'created': datetime.datetime(2012, 08, 22, 16, 20, 09, 822243)}

## Saving instances

If we want to be able to return complete object instances based on the validated data we need to implement one or both of the `.create()` and `update()` methods. For example:

    class CommentSerializer(serializers.Serializer):
        email = serializers.EmailField()
        content = serializers.CharField(max_length=200)
        created = serializers.DateTimeField()

        def create(self, validated_data):
            return Comment(**validated_data)

        def update(self, instance, validated_data):
            instance.email = validated_data.get('email', instance.email)
            instance.content = validated_data.get('content', instance.content)
            instance.created = validated_data.get('created', instance.created)
            return instance

If your object instances correspond to Django models you'll also want to ensure that these methods save the object to the database. For example, if `Comment` was a Django model, the methods might look like this:

        def create(self, validated_data):
            return Comment.objcts.create(**validated_data)

        def update(self, instance, validated_data):
            instance.email = validated_data.get('email', instance.email)
            instance.content = validated_data.get('content', instance.content)
            instance.created = validated_data.get('created', instance.created)
            instance.save()
            return instance
 
Now when deserializing data, we can call `.save()` to return an object instance, based on the validated data.

    comment = serializer.save()

Calling `.save()` will either create a new instance, or update an existing instance, depending on if an existing instance was passed when instantiating the serializer class:

    # .save() will create a new instance.
    serializer = CommentSerializer(data=data)
    
    # .save() will update the existing `comment` instance.
    serializer = CommentSerializer(comment, data=data)

Both the `.create()` and `.update()` methods are optional. You can implement either neither, one, or both of them, depending on the use-case for your serializer class.

#### Passing additional attributes to `.save()`

Sometimes you'll want your view code to be able to inject additional data at the point of saving the instance. This additional data might include information like the current user, the current time, or anything else that is not part of the request data.

You can do so by including additional keyword arguments when calling `.save()`. For example:

    serializer.save(owner=request.user)

Any additional keyword arguments will be included in the `validated_data` argument when `.create()` or `.update()` are called.

#### Overriding `.save()` directly.

In some cases the `.create()` and `.update()` method names may not be meaningful. For example, in a contact form we may not be creating new instances, but instead sending an email or other message.

In these cases you might instead choose to override `.save()` directly, as being more readable and meaningful.

For example:

    class ContactForm(serializers.Serializer):
        email = serializers.EmailField()
        message = serializers.CharField()
        
        def save(self):
            email = self.validated_data['email']
            message = self.validated_data['message']
            send_email(from=email, message=message)

Note that in the case above we're now having to access the serializer `.validated_data` property directly.

## Validation

When deserializing data, you always need to call `is_valid()` before attempting to access the validated data, or save an object instance. If any validation errors occur, the `.errors` property will contain a dictionary representing the resulting error messages.  For example:

    serializer = CommentSerializer(data={'email': 'foobar', 'content': 'baz'})
    serializer.is_valid()
    # False
    serializer.errors
    # {'email': [u'Enter a valid e-mail address.'], 'created': [u'This field is required.']}

Each key in the dictionary will be the field name, and the values will be lists of strings of any error messages corresponding to that field.  The `non_field_errors` key may also be present, and will list any general validation errors. The name of the `non_field_errors` key may be customized using the `NON_FIELD_ERRORS_KEY` REST framework setting.

When deserializing a list of items, errors will be returned as a list of dictionaries representing each of the deserialized items.

#### Raising an exception on invalid data

The `.is_valid()` method takes an optional `raise_exception` flag that will cause it to raise a `serializers.ValidationError` exception if there are validation errors.

These exceptions are automatically dealt with by the default exception handler that REST framework provides, and will return `HTTP 400 Bad Request` responses by default.

    # Return a 400 response if the data was invalid.
    serializer.is_valid(raise_exception=True)

#### Field-level validation

You can specify custom field-level validation by adding `.validate_<fieldname>` methods to your `Serializer` subclass.  These are similar to the `.clean_<fieldname>` methods on Django forms.

These methods take a single argument, which is the field value that requires validation.

Your `validate_<fieldname>` methods should return the validated value or raise a `ValidationError`.  For example:

    from rest_framework import serializers

    class BlogPostSerializer(serializers.Serializer):
        title = serializers.CharField(max_length=100)
        content = serializers.CharField()

        def validate_title(self, value):
            """
            Check that the blog post is about Django.
            """
            if 'django' not in value.lower():
                raise serializers.ValidationError("Blog post is not about Django")
            return value

#### Object-level validation

To do any other validation that requires access to multiple fields, add a method called `.validate()` to your `Serializer` subclass.  This method takes a single argument, which is a dictionary of field values.  It should raise a `ValidationError` if necessary, or just return the validated values.  For example:

    from rest_framework import serializers

    class EventSerializer(serializers.Serializer):
        description = serializers.CharField(max_length=100)
        start = serializers.DateTimeField()
        finish = serializers.DateTimeField()

        def validate(self, data):
            """
            Check that the start is before the stop.
            """
            if data['start'] > data['finish']:
                raise serializers.ValidationError("finish must occur after start")
            return data

#### Validators

Individual fields on a serializer can include validators, by declaring them on the field instance, for example:

    def multiple_of_ten(value):
        if value % 10 != 0:
            raise serializers.ValidationError('Not a multiple of ten')

    class GameRecord(serializers.Serializer):
        score = IntegerField(validators=[multiple_of_ten])
        ...

Serializer classes can also include reusable validators that are applied to the complete set of field data. These validators are included by declaring them on an inner `Meta` class, like so:

    class EventSerializer(serializers.Serializer):
        name = serializers.CharField()
        room_number = serializers.IntegerField(choices=[101, 102, 103, 201])
        date = serializers.DateField()
        
        class Meta:
            # Each room only has one event per day.
            validators = UniqueTogetherValidator(
                queryset=Event.objects.all(),
                fields=['room_number', 'date']
            )

For more information see the [validators documentation](validators.md).

## Partial updates

By default, serializers must be passed values for all required fields or they will raise validation errors. You can use the `partial` argument in order to allow partial updates.

    # Update `comment` with partial data
    serializer = CommentSerializer(comment, data={'content': u'foo bar'}, partial=True)

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

Similarly if a nested representation should be a list of items, you should pass the `many=True` flag to the nested serialized.

    class CommentSerializer(serializers.Serializer):
        user = UserSerializer(required=False)
        edits = EditItemSerializer(many=True)  # A nested list of 'edit' items.
        content = serializers.CharField(max_length=200)
        created = serializers.DateTimeField()

Validation of nested objects will work the same as before.  Errors with nested objects will be nested under the field name of the nested object.

    serializer = CommentSerializer(data={'user': {'email': 'foobar', 'username': 'doe'}, 'content': 'baz'})
    serializer.is_valid()
    # False
    serializer.errors
    # {'user': {'email': [u'Enter a valid e-mail address.']}, 'created': [u'This field is required.']}

**TODO** Document create and update for nested serializers

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

**TODO**

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

**TODO**

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
    serializer.save()  # `.save()` will be called on each updated or newly created instance.

By default bulk updates will be limited to updating instances that already exist in the provided queryset.

When performing a bulk update you may want to allow new items to be created, and missing items to be deleted.  To do so, pass `allow_add_remove=True` to the serializer.

    serializer = BookSerializer(queryset, data=data, many=True, allow_add_remove=True)
    serializer.is_valid()
    # True
    serializer.save()  # `.save()` will be called on updated or newly created instances.
                       # `.delete()` will be called on any other items in the `queryset`.

Passing `allow_add_remove=True` ensures that any update operations will completely overwrite the existing queryset, rather than simply updating existing objects.

## Including extra context

There are some cases where you need to provide extra context to the serializer in addition to the object being serialized.  One common case is if you're using a serializer that includes hyperlinked relations, which requires the serializer to have access to the current request so that it can properly generate fully qualified URLs.

You can provide arbitrary additional context by passing a `context` argument when instantiating the serializer.  For example:

    serializer = AccountSerializer(account, context={'request': request})
    serializer.data
    # {'id': 6, 'owner': u'denvercoder9', 'created': datetime.datetime(2013, 2, 12, 09, 44, 56, 678870), 'details': 'http://example.com/accounts/6/details'}

The context dictionary can be used within any serializer field logic, such as a custom `.to_representation()` method, by accessing the `self.context` attribute.

---

# ModelSerializer

Often you'll want serializer classes that map closely to Django model definitions.

The `ModelSerializer` class provides a shortcut that lets you automatically create a `Serializer` class with fields that correspond to the Model fields.

**The `ModelSerializer` class is the same as a regular `Serializer` class, except that**:

* It will automatically generate a set of fields for you, based on the model.
* It will automatically generate validators for the serializer, such as unique_together validators.
* It includes simple default implementations of `.create()` and `.update()`.

Declaring a `ModelSerializer` looks like this:

    class AccountSerializer(serializers.ModelSerializer):
        class Meta:
            model = Account

By default, all the model fields on the class will be mapped to a corresponding serializer fields.

Any relationships such as foreign keys on the model will be mapped to `PrimaryKeyRelatedField`. Reverse relationships are not included by default unless explicitly included as described below.

#### Inspecting the generated `ModelSerializer` class.

Serializer classes generate helpful verbose representation strings, that allow you to fully inspect the state of their fields. This is particularly useful when working with `ModelSerializers` where you want to determine what set of fields and validators are being automatically created for you.

To do so, open the Django shell, using `python manage.py shell`, then import the serializer class, instantiate it, and print the object representation…

    >>> from myapp.serializers import AccountSerializer
    >>> serializer = AccountSerializer()
    >>> print repr(serializer)  # Or `print(repr(serializer))` in Python 3.x.
    AccountSerializer():
        id = IntegerField(label='ID', read_only=True)
        name = CharField(allow_blank=True, max_length=100, required=False)
        owner = PrimaryKeyRelatedField(queryset=User.objects.all())
 
## Specifying which fields should be included

If you only want a subset of the default fields to be used in a model serializer, you can do so using `fields` or `exclude` options, just as you would with a `ModelForm`.

For example:

    class AccountSerializer(serializers.ModelSerializer):
        class Meta:
            model = Account
            fields = ('id', 'account_name', 'users', 'created')

The names in the `fields` option will normally map to model fields on the model class.

Alternatively names in the `fields` options can map to properties or methods which take no arguments that exist on the model class.

## Specifying nested serialization

The default `ModelSerializer` uses primary keys for relationships, but you can also easily generate nested representations using the `depth` option:

    class AccountSerializer(serializers.ModelSerializer):
        class Meta:
            model = Account
            fields = ('id', 'account_name', 'users', 'created')
            depth = 1

The `depth` option should be set to an integer value that indicates the depth of relationships that should be traversed before reverting to a flat representation.

If you want to customize the way the serialization is done (e.g. using `allow_add_remove`) you'll need to define the field yourself.

## Specifying fields explicitly

You can add extra fields to a `ModelSerializer` or override the default fields by declaring fields on the class, just as you would for a `Serializer` class.

    class AccountSerializer(serializers.ModelSerializer):
        url = serializers.CharField(source='get_absolute_url', read_only=True)
        groups = serializers.PrimaryKeyRelatedField(many=True)

        class Meta:
            model = Account

Extra fields can correspond to any property or callable on the model.

## Specifying which fields should be read-only

You may wish to specify multiple fields as read-only. Instead of adding each field explicitly with the `read_only=True` attribute, you may use the shortcut Meta option, `read_only_fields`.

This option should be a list or tuple of field names, and is declared as follows:

    class AccountSerializer(serializers.ModelSerializer):
        class Meta:
            model = Account
            fields = ('id', 'account_name', 'users', 'created')
            read_only_fields = ('account_name',)

Model fields which have `editable=False` set, and `AutoField` fields will be set to read-only by default, and do not need to be added to the `read_only_fields` option.

## Specifying additional keyword arguments for fields.

There is also a shortcut allowing you to specify arbitrary additional keyword arguments on fields, using the `extra_kwargs` option. Similarly to `read_only_fields` this means you do not need to explicitly declare the field on the serializer.

This option is a dictionary, mapping field names to a dictionary of keyword arguments. For example:

    class CreateUserSerializer(serializers.ModelSerializer):
        class Meta:
            model = User
            fields = ('email', 'username', 'password')
            extra_kwargs = {'password': {'write_only': True}}
            
        def create(self, validated_data):
            user = User(
                email=validated_data['email'],
                username=validated_data['username']
            )
            user.set_password(validated_data['password'])
            user.save()
            return user

## Relational fields

When serializing model instances, there are a number of different ways you might choose to represent relationships.  The default representation for `ModelSerializer` is to use the primary keys of the related instances.

Alternative representations include serializing using hyperlinks, serializing complete nested representations, or serializing with a custom representation.

For full details see the [serializer relations][relations] documentation.

## Inheritance of the 'Meta' class

The inner `Meta` class on serializers is not inherited from parent classes by default. This is the same behavior as with Django's `Model` and `ModelForm` classes. If you want the `Meta` class to inherit from a parent class you must do so explicitly. For example:

    class AccountSerializer(MyBaseSerializer):
        class Meta(MyBaseSerializer.Meta):
            model = Account

Typically we would recommend *not* using inheritance on inner Meta classes, but instead declaring all options explicitly.

---

# HyperlinkedModelSerializer

The `HyperlinkedModelSerializer` class is similar to the `ModelSerializer` class except that it uses hyperlinks to represent relationships, rather than primary keys.

By default the serializer will include a `url` field instead of a primary key field.

The url field will be represented using a `HyperlinkedIdentityField` serializer field, and any relationships on the model will be represented using a `HyperlinkedRelatedField` serializer field.

You can explicitly include the primary key by adding it to the `fields` option, for example:

    class AccountSerializer(serializers.HyperlinkedModelSerializer):
        class Meta:
            model = Account
            fields = ('url', 'id', 'account_name', 'users', 'created')

## How hyperlinked views are determined

There needs to be a way of determining which views should be used for hyperlinking to model instances.

By default hyperlinks are expected to correspond to a view name that matches the style `'{model_name}-detail'`, and looks up the instance by a `pk` keyword argument.

You can change the field that is used for object lookups by setting the `lookup_field` option. The value of this option should correspond both with a kwarg in the URL conf, and with a field on the model.  For example:

    class AccountSerializer(serializers.HyperlinkedModelSerializer):
        class Meta:
            model = Account
            fields = ('url', 'account_name', 'users', 'created')
            lookup_field = 'slug'

Note that the `lookup_field` will be used as the default on *all* hyperlinked fields, including both the URL identity, and any hyperlinked relationships.

For more specific requirements such as specifying a different lookup for each field, you'll want to set the fields on the serializer explicitly.  For example:

    class AccountSerializer(serializers.HyperlinkedModelSerializer):
        url = serializers.HyperlinkedIdentityField(
            view_name='account-detail',
            lookup_field='slug'
        )
        users = serializers.HyperlinkedRelatedField(
            view_name='user-detail',
            lookup_field='username',
            many=True,
            read_only=True
        )

        class Meta:
            model = Account
            fields = ('url', 'account_name', 'users', 'created')

## Overriding the URL field behavior

The name of the URL field defaults to 'url'.  You can override this globally, by using the `URL_FIELD_NAME` setting.

You can also override this on a per-serializer basis by using the `url_field_name` option on the serializer, like so:

    class AccountSerializer(serializers.HyperlinkedModelSerializer):
        class Meta:
            model = Account
            fields = ('account_url', 'account_name', 'users', 'created')
            url_field_name = 'account_url'

**Note**: The generic view implementations normally generate a `Location` header in response to successful `POST` requests. Serializers using `url_field_name` option will not have this header automatically included by the view.  If you need to do so you will ned to also override the view's `get_success_headers()` method.

You can also override the URL field's view name and lookup field without overriding the field explicitly, by using the `view_name` and `lookup_field` options, like so:

    class AccountSerializer(serializers.HyperlinkedModelSerializer):
        class Meta:
            model = Account
            fields = ('account_url', 'account_name', 'users', 'created')
            view_name = 'account_detail'
            lookup_field='account_name'

---

**TODO**: ListSerializer, BaseSerializer, overriding `to_representation` on serializers.

# Advanced serializer usage

**TODO**: Tweak section below

You can create customized subclasses of `ModelSerializer` or `HyperlinkedModelSerializer` that use a different set of default fields.

Doing so should be considered advanced usage, and will only be needed if you have some particular serializer requirements that you often need to repeat.

## Dynamically modifying fields

Once a serializer has been initialized, the dictionary of fields that are set on the serializer may be accessed using the `.fields` attribute.  Accessing and modifying this attribute allows you to dynamically modify the serializer.

Modifying the `fields` argument directly allows you to do interesting things such as changing the arguments on serializer fields at runtime, rather than at the point of declaring the serializer.

### Example

For example, if you wanted to be able to set which fields should be used by a serializer at the point of initializing it, you could create a serializer class like so:

    class DynamicFieldsModelSerializer(serializers.ModelSerializer):
        """
        A ModelSerializer that takes an additional `fields` argument that
        controls which fields should be displayed.
        """

        def __init__(self, *args, **kwargs):
            # Don't pass the 'fields' arg up to the superclass
            fields = kwargs.pop('fields', None)

            # Instantiate the superclass normally
            super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

            if fields is not None:
                # Drop any fields that are not specified in the `fields` argument.
                allowed = set(fields)
                existing = set(self.fields.keys())
                for field_name in existing - allowed:
                    self.fields.pop(field_name)

This would then allow you to do the following:

    >>> class UserSerializer(DynamicFieldsModelSerializer):
    >>>     class Meta:
    >>>         model = User
    >>>         fields = ('id', 'username', 'email')
    >>>
    >>> print UserSerializer(user)
    {'id': 2, 'username': 'jonwatts', 'email': 'jon@example.com'}
    >>>
    >>> print UserSerializer(user, fields=('id', 'email'))
    {'id': 2, 'email': 'jon@example.com'}

## Customizing the default fields

**TODO**: Remove and note incoming API.

The `field_mapping` attribute is a dictionary that maps model classes to serializer classes.  Overriding the attribute will let you set a different set of default serializer classes.

For more advanced customization than simply changing the default serializer class you can override various `get_<field_type>_field` methods.  Doing so will allow you to customize the arguments that each serializer field is initialized with.  Each of these methods may either return a field or serializer instance, or `None`.

### get_pk_field

**Signature**: `.get_pk_field(self, model_field)`

Returns the field instance that should be used to represent the pk field.

### get_nested_field

**Signature**: `.get_nested_field(self, model_field, related_model, to_many)`

Returns the field instance that should be used to represent a related field when `depth` is specified as being non-zero.

Note that the `model_field` argument will be `None` for reverse relationships.  The `related_model` argument will be the model class for the target of the field.  The `to_many` argument will be a boolean indicating if this is a to-one or to-many relationship.

### get_related_field

**Signature**: `.get_related_field(self, model_field, related_model, to_many)`

Returns the field instance that should be used to represent a related field when `depth` is not specified, or when nested representations are being used and the depth reaches zero.

Note that the `model_field` argument will be `None` for reverse relationships.  The `related_model` argument will be the model class for the target of the field.  The `to_many` argument will be a boolean indicating if this is a to-one or to-many relationship.

### get_field

**Signature**: `.get_field(self, model_field)`

Returns the field instance that should be used for non-relational, non-pk fields.

### Example

The following custom model serializer could be used as a base class for model serializers that should always exclude the pk by default.

    class NoPKModelSerializer(serializers.ModelSerializer):
        def get_pk_field(self, model_field):
            return None

---

# Third party packages

The following third party packages are also available.

## MongoengineModelSerializer

The [django-rest-framework-mongoengine][mongoengine] package provides a `MongoEngineModelSerializer` serializer class that supports using MongoDB as the storage layer for Django REST framework.

## GeoFeatureModelSerializer

The [django-rest-framework-gis][django-rest-framework-gis] package provides a `GeoFeatureModelSerializer` serializer class that supports GeoJSON both for read and write operations.

## HStoreSerializer

The [django-rest-framework-hstore][django-rest-framework-hstore] package provides an `HStoreSerializer` to support [django-hstore][django-hstore] `DictionaryField` model field and its `schema-mode` feature.

[cite]: https://groups.google.com/d/topic/django-users/sVFaOfQi4wY/discussion
[relations]: relations.md
[mongoengine]: https://github.com/umutbozkurt/django-rest-framework-mongoengine
[django-rest-framework-gis]: https://github.com/djangonauts/django-rest-framework-gis
[django-rest-framework-hstore]: https://github.com/djangonauts/django-rest-framework-hstore
[django-hstore]: https://github.com/djangonauts/django-hstore
