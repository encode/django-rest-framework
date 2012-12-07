import datetime, pickle
from django.test import TestCase
from rest_framework import serializers
from rest_framework.tests.models import (Album, ActionItem, Anchor, BasicModel,
    BlankFieldModel, BlogPost, Book, CallableDefaultValueModel, DefaultValueModel,
    ManyToManyModel, Person, ReadOnlyManyToManyModel)


class SubComment(object):
    def __init__(self, sub_comment):
        self.sub_comment = sub_comment


class Comment(object):
    def __init__(self, email, content, created):
        self.email = email
        self.content = content
        self.created = created or datetime.datetime.now()

    def __eq__(self, other):
        return all([getattr(self, attr) == getattr(other, attr)
                    for attr in ('email', 'content', 'created')])

    def get_sub_comment(self):
        sub_comment = SubComment('And Merry Christmas!')
        return sub_comment


class CommentSerializer(serializers.Serializer):
    email = serializers.EmailField()
    content = serializers.CharField(max_length=1000)
    created = serializers.DateTimeField()
    sub_comment = serializers.Field(source='get_sub_comment.sub_comment')

    def restore_object(self, data, instance=None):
        if instance is None:
            return Comment(**data)
        for key, val in data.items():
            setattr(instance, key, val)
        return instance


class BookSerializer(serializers.ModelSerializer):
    isbn = serializers.RegexField(regex=r'^[0-9]{13}$', error_messages={'invalid': 'isbn has to be exact 13 numbers'})

    class Meta:
        model = Book


class ActionItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = ActionItem


class PersonSerializer(serializers.ModelSerializer):
    info = serializers.Field(source='info')

    class Meta:
        model = Person
        fields = ('name', 'age', 'info')
        read_only_fields = ('age',)


class AlbumsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Album


class BasicTests(TestCase):
    def setUp(self):
        self.comment = Comment(
            'tom@example.com',
            'Happy new year!',
            datetime.datetime(2012, 1, 1)
        )
        self.data = {
            'email': 'tom@example.com',
            'content': 'Happy new year!',
            'created': datetime.datetime(2012, 1, 1),
            'sub_comment': 'This wont change'
        }
        self.expected = {
            'email': 'tom@example.com',
            'content': 'Happy new year!',
            'created': datetime.datetime(2012, 1, 1),
            'sub_comment': 'And Merry Christmas!'
        }
        self.person_data = {'name': 'dwight', 'age': 35}
        self.person = Person(**self.person_data)
        self.person.save()

    def test_empty(self):
        serializer = CommentSerializer()
        expected = {
            'email': '',
            'content': '',
            'created': None,
            'sub_comment': ''
        }
        self.assertEquals(serializer.data, expected)

    def test_retrieve(self):
        serializer = CommentSerializer(self.comment)
        self.assertEquals(serializer.data, self.expected)

    def test_create(self):
        serializer = CommentSerializer(data=self.data)
        expected = self.comment
        self.assertEquals(serializer.is_valid(), True)
        self.assertEquals(serializer.object, expected)
        self.assertFalse(serializer.object is expected)
        self.assertEquals(serializer.data['sub_comment'], 'And Merry Christmas!')

    def test_update(self):
        serializer = CommentSerializer(self.comment, data=self.data)
        expected = self.comment
        self.assertEquals(serializer.is_valid(), True)
        self.assertEquals(serializer.object, expected)
        self.assertTrue(serializer.object is expected)
        self.assertEquals(serializer.data['sub_comment'], 'And Merry Christmas!')

    def test_partial_update(self):
        msg = 'Merry New Year!'
        partial_data = {'content': msg}
        serializer = CommentSerializer(self.comment, data=partial_data)
        self.assertEquals(serializer.is_valid(), False)
        serializer = CommentSerializer(self.comment, data=partial_data, partial=True)
        expected = self.comment
        self.assertEqual(serializer.is_valid(), True)
        self.assertEquals(serializer.object, expected)
        self.assertTrue(serializer.object is expected)
        self.assertEquals(serializer.data['content'], msg)

    def test_model_fields_as_expected(self):
        """
        Make sure that the fields returned are the same as defined
        in the Meta data
        """
        serializer = PersonSerializer(self.person)
        self.assertEquals(set(serializer.data.keys()),
                          set(['name', 'age', 'info']))

    def test_field_with_dictionary(self):
        """
        Make sure that dictionaries from fields are left intact
        """
        serializer = PersonSerializer(self.person)
        expected = self.person_data
        self.assertEquals(serializer.data['info'], expected)

    def test_read_only_fields(self):
        """
        Attempting to update fields set as read_only should have no effect.
        """

        serializer = PersonSerializer(self.person, data={'name': 'dwight', 'age': 99})
        self.assertEquals(serializer.is_valid(), True)
        instance = serializer.save()
        self.assertEquals(serializer.errors, {})
        # Assert age is unchanged (35)
        self.assertEquals(instance.age, self.person_data['age'])


class ValidationTests(TestCase):
    def setUp(self):
        self.comment = Comment(
            'tom@example.com',
            'Happy new year!',
            datetime.datetime(2012, 1, 1)
        )
        self.data = {
            'email': 'tom@example.com',
            'content': 'x' * 1001,
            'created': datetime.datetime(2012, 1, 1)
        }
        self.actionitem = ActionItem(title='Some to do item',
        )

    def test_create(self):
        serializer = CommentSerializer(data=self.data)
        self.assertEquals(serializer.is_valid(), False)
        self.assertEquals(serializer.errors, {'content': [u'Ensure this value has at most 1000 characters (it has 1001).']})

    def test_update(self):
        serializer = CommentSerializer(self.comment, data=self.data)
        self.assertEquals(serializer.is_valid(), False)
        self.assertEquals(serializer.errors, {'content': [u'Ensure this value has at most 1000 characters (it has 1001).']})

    def test_update_missing_field(self):
        data = {
            'content': 'xxx',
            'created': datetime.datetime(2012, 1, 1)
        }
        serializer = CommentSerializer(self.comment, data=data)
        self.assertEquals(serializer.is_valid(), False)
        self.assertEquals(serializer.errors, {'email': [u'This field is required.']})

    def test_missing_bool_with_default(self):
        """Make sure that a boolean value with a 'False' value is not
        mistaken for not having a default."""
        data = {
            'title': 'Some action item',
            #No 'done' value.
        }
        serializer = ActionItemSerializer(self.actionitem, data=data)
        self.assertEquals(serializer.is_valid(), True)
        self.assertEquals(serializer.errors, {})

    def test_field_validation(self):

        class CommentSerializerWithFieldValidator(CommentSerializer):

            def validate_content(self, attrs, source):
                value = attrs[source]
                if "test" not in value:
                    raise serializers.ValidationError("Test not in value")
                return attrs

        data = {
            'email': 'tom@example.com',
            'content': 'A test comment',
            'created': datetime.datetime(2012, 1, 1)
        }

        serializer = CommentSerializerWithFieldValidator(data=data)
        self.assertTrue(serializer.is_valid())

        data['content'] = 'This should not validate'

        serializer = CommentSerializerWithFieldValidator(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertEquals(serializer.errors, {'content': [u'Test not in value']})

    def test_cross_field_validation(self):

        class CommentSerializerWithCrossFieldValidator(CommentSerializer):

            def validate(self, attrs):
                if attrs["email"] not in attrs["content"]:
                    raise serializers.ValidationError("Email address not in content")
                return attrs

        data = {
            'email': 'tom@example.com',
            'content': 'A comment from tom@example.com',
            'created': datetime.datetime(2012, 1, 1)
        }

        serializer = CommentSerializerWithCrossFieldValidator(data=data)
        self.assertTrue(serializer.is_valid())

        data['content'] = 'A comment from foo@bar.com'

        serializer = CommentSerializerWithCrossFieldValidator(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertEquals(serializer.errors, {'non_field_errors': [u'Email address not in content']})

    def test_null_is_true_fields(self):
        """
        Omitting a value for null-field should validate.
        """
        serializer = PersonSerializer(data={'name': 'marko'})
        self.assertEquals(serializer.is_valid(), True)
        self.assertEquals(serializer.errors, {})

    def test_modelserializer_max_length_exceeded(self):
        data = {
            'title': 'x' * 201,
        }
        serializer = ActionItemSerializer(data=data)
        self.assertEquals(serializer.is_valid(), False)
        self.assertEquals(serializer.errors, {'title': [u'Ensure this value has at most 200 characters (it has 201).']})

    def test_default_modelfield_max_length_exceeded(self):
        data = {
            'title': 'Testing "info" field...',
            'info': 'x' * 13,
        }
        serializer = ActionItemSerializer(data=data)
        self.assertEquals(serializer.is_valid(), False)
        self.assertEquals(serializer.errors, {'info': [u'Ensure this value has at most 12 characters (it has 13).']})

    def test_validate_unique(self):
        """
        Just check if serializers.ModelSerializer.perform_model_validation() handles unique checks via .full_clean()
        """
        serializer = AlbumsSerializer(data={'title': 'a'})
        serializer.is_valid()
        serializer.save()
        second_serializer = AlbumsSerializer(data={'title': 'a'})
        self.assertFalse(second_serializer.is_valid())
        self.assertEqual(second_serializer.errors,  {'title': [u'Album with this Title already exists.']})


class RegexValidationTest(TestCase):
    def test_create_failed(self):
        serializer = BookSerializer(data={'isbn': '1234567890'})
        self.assertFalse(serializer.is_valid())
        self.assertEquals(serializer.errors, {'isbn': [u'isbn has to be exact 13 numbers']})

        serializer = BookSerializer(data={'isbn': '12345678901234'})
        self.assertFalse(serializer.is_valid())
        self.assertEquals(serializer.errors, {'isbn': [u'isbn has to be exact 13 numbers']})

        serializer = BookSerializer(data={'isbn': 'abcdefghijklm'})
        self.assertFalse(serializer.is_valid())
        self.assertEquals(serializer.errors, {'isbn': [u'isbn has to be exact 13 numbers']})

    def test_create_success(self):
        serializer = BookSerializer(data={'isbn': '1234567890123'})
        self.assertTrue(serializer.is_valid())


class MetadataTests(TestCase):
    def test_empty(self):
        serializer = CommentSerializer()
        expected = {
            'email': serializers.CharField,
            'content': serializers.CharField,
            'created': serializers.DateTimeField
        }
        for field_name, field in expected.items():
            self.assertTrue(isinstance(serializer.data.fields[field_name], field))


class ManyToManyTests(TestCase):
    def setUp(self):
        class ManyToManySerializer(serializers.ModelSerializer):
            class Meta:
                model = ManyToManyModel

        self.serializer_class = ManyToManySerializer

        # An anchor instance to use for the relationship
        self.anchor = Anchor()
        self.anchor.save()

        # A model instance with a many to many relationship to the anchor
        self.instance = ManyToManyModel()
        self.instance.save()
        self.instance.rel.add(self.anchor)

        # A serialized representation of the model instance
        self.data = {'id': 1, 'rel': [self.anchor.id]}

    def test_retrieve(self):
        """
        Serialize an instance of a model with a ManyToMany relationship.
        """
        serializer = self.serializer_class(instance=self.instance)
        expected = self.data
        self.assertEquals(serializer.data, expected)

    def test_create(self):
        """
        Create an instance of a model with a ManyToMany relationship.
        """
        data = {'rel': [self.anchor.id]}
        serializer = self.serializer_class(data=data)
        self.assertEquals(serializer.is_valid(), True)
        instance = serializer.save()
        self.assertEquals(len(ManyToManyModel.objects.all()), 2)
        self.assertEquals(instance.pk, 2)
        self.assertEquals(list(instance.rel.all()), [self.anchor])

    def test_update(self):
        """
        Update an instance of a model with a ManyToMany relationship.
        """
        new_anchor = Anchor()
        new_anchor.save()
        data = {'rel': [self.anchor.id, new_anchor.id]}
        serializer = self.serializer_class(self.instance, data=data)
        self.assertEquals(serializer.is_valid(), True)
        instance = serializer.save()
        self.assertEquals(len(ManyToManyModel.objects.all()), 1)
        self.assertEquals(instance.pk, 1)
        self.assertEquals(list(instance.rel.all()), [self.anchor, new_anchor])

    def test_create_empty_relationship(self):
        """
        Create an instance of a model with a ManyToMany relationship,
        containing no items.
        """
        data = {'rel': []}
        serializer = self.serializer_class(data=data)
        self.assertEquals(serializer.is_valid(), True)
        instance = serializer.save()
        self.assertEquals(len(ManyToManyModel.objects.all()), 2)
        self.assertEquals(instance.pk, 2)
        self.assertEquals(list(instance.rel.all()), [])

    def test_update_empty_relationship(self):
        """
        Update an instance of a model with a ManyToMany relationship,
        containing no items.
        """
        new_anchor = Anchor()
        new_anchor.save()
        data = {'rel': []}
        serializer = self.serializer_class(self.instance, data=data)
        self.assertEquals(serializer.is_valid(), True)
        instance = serializer.save()
        self.assertEquals(len(ManyToManyModel.objects.all()), 1)
        self.assertEquals(instance.pk, 1)
        self.assertEquals(list(instance.rel.all()), [])

    def test_create_empty_relationship_flat_data(self):
        """
        Create an instance of a model with a ManyToMany relationship,
        containing no items, using a representation that does not support
        lists (eg form data).
        """
        data = {'rel': ''}
        serializer = self.serializer_class(data=data)
        self.assertEquals(serializer.is_valid(), True)
        instance = serializer.save()
        self.assertEquals(len(ManyToManyModel.objects.all()), 2)
        self.assertEquals(instance.pk, 2)
        self.assertEquals(list(instance.rel.all()), [])


class ReadOnlyManyToManyTests(TestCase):
    def setUp(self):
        class ReadOnlyManyToManySerializer(serializers.ModelSerializer):
            rel = serializers.ManyRelatedField(read_only=True)

            class Meta:
                model = ReadOnlyManyToManyModel

        self.serializer_class = ReadOnlyManyToManySerializer

        # An anchor instance to use for the relationship
        self.anchor = Anchor()
        self.anchor.save()

        # A model instance with a many to many relationship to the anchor
        self.instance = ReadOnlyManyToManyModel()
        self.instance.save()
        self.instance.rel.add(self.anchor)

        # A serialized representation of the model instance
        self.data = {'rel': [self.anchor.id], 'id': 1, 'text': 'anchor'}

    def test_update(self):
        """
        Attempt to update an instance of a model with a ManyToMany
        relationship.  Not updated due to read_only=True
        """
        new_anchor = Anchor()
        new_anchor.save()
        data = {'rel': [self.anchor.id, new_anchor.id]}
        serializer = self.serializer_class(self.instance, data=data)
        self.assertEquals(serializer.is_valid(), True)
        instance = serializer.save()
        self.assertEquals(len(ReadOnlyManyToManyModel.objects.all()), 1)
        self.assertEquals(instance.pk, 1)
        # rel is still as original (1 entry)
        self.assertEquals(list(instance.rel.all()), [self.anchor])

    def test_update_without_relationship(self):
        """
        Attempt to update an instance of a model where many to ManyToMany
        relationship is not supplied.  Not updated due to read_only=True
        """
        new_anchor = Anchor()
        new_anchor.save()
        data = {}
        serializer = self.serializer_class(self.instance, data=data)
        self.assertEquals(serializer.is_valid(), True)
        instance = serializer.save()
        self.assertEquals(len(ReadOnlyManyToManyModel.objects.all()), 1)
        self.assertEquals(instance.pk, 1)
        # rel is still as original (1 entry)
        self.assertEquals(list(instance.rel.all()), [self.anchor])


class DefaultValueTests(TestCase):
    def setUp(self):
        class DefaultValueSerializer(serializers.ModelSerializer):
            class Meta:
                model = DefaultValueModel

        self.serializer_class = DefaultValueSerializer
        self.objects = DefaultValueModel.objects

    def test_create_using_default(self):
        data = {}
        serializer = self.serializer_class(data=data)
        self.assertEquals(serializer.is_valid(), True)
        instance = serializer.save()
        self.assertEquals(len(self.objects.all()), 1)
        self.assertEquals(instance.pk, 1)
        self.assertEquals(instance.text, 'foobar')

    def test_create_overriding_default(self):
        data = {'text': 'overridden'}
        serializer = self.serializer_class(data=data)
        self.assertEquals(serializer.is_valid(), True)
        instance = serializer.save()
        self.assertEquals(len(self.objects.all()), 1)
        self.assertEquals(instance.pk, 1)
        self.assertEquals(instance.text, 'overridden')


class CallableDefaultValueTests(TestCase):
    def setUp(self):
        class CallableDefaultValueSerializer(serializers.ModelSerializer):
            class Meta:
                model = CallableDefaultValueModel

        self.serializer_class = CallableDefaultValueSerializer
        self.objects = CallableDefaultValueModel.objects

    def test_create_using_default(self):
        data = {}
        serializer = self.serializer_class(data=data)
        self.assertEquals(serializer.is_valid(), True)
        instance = serializer.save()
        self.assertEquals(len(self.objects.all()), 1)
        self.assertEquals(instance.pk, 1)
        self.assertEquals(instance.text, 'foobar')

    def test_create_overriding_default(self):
        data = {'text': 'overridden'}
        serializer = self.serializer_class(data=data)
        self.assertEquals(serializer.is_valid(), True)
        instance = serializer.save()
        self.assertEquals(len(self.objects.all()), 1)
        self.assertEquals(instance.pk, 1)
        self.assertEquals(instance.text, 'overridden')


class ManyRelatedTests(TestCase):
    def test_reverse_relations(self):
        post = BlogPost.objects.create(title="Test blog post")
        post.blogpostcomment_set.create(text="I hate this blog post")
        post.blogpostcomment_set.create(text="I love this blog post")

        class BlogPostCommentSerializer(serializers.Serializer):
            text = serializers.CharField()

        class BlogPostSerializer(serializers.Serializer):
            title = serializers.CharField()
            comments = BlogPostCommentSerializer(source='blogpostcomment_set')

        serializer = BlogPostSerializer(instance=post)
        expected = {
            'title': 'Test blog post',
            'comments': [
                {'text': 'I hate this blog post'},
                {'text': 'I love this blog post'}
            ]
        }

        self.assertEqual(serializer.data, expected)

    def test_callable_source(self):
        post = BlogPost.objects.create(title="Test blog post")
        post.blogpostcomment_set.create(text="I love this blog post")

        class BlogPostCommentSerializer(serializers.Serializer):
            text = serializers.CharField()

        class BlogPostSerializer(serializers.Serializer):
            title = serializers.CharField()
            first_comment = BlogPostCommentSerializer(source='get_first_comment')

        serializer = BlogPostSerializer(post)

        expected = {
            'title': 'Test blog post',
            'first_comment': {'text': 'I love this blog post'}
        }
        self.assertEqual(serializer.data, expected)


class RelatedTraversalTest(TestCase):
    def test_nested_traversal(self):
        user = Person.objects.create(name="django")
        post = BlogPost.objects.create(title="Test blog post", writer=user)
        post.blogpostcomment_set.create(text="I love this blog post")

        from rest_framework.tests.models import BlogPostComment

        class PersonSerializer(serializers.ModelSerializer):
            class Meta:
                model = Person
                fields = ("name", "age")

        class BlogPostCommentSerializer(serializers.ModelSerializer):
            class Meta:
                model = BlogPostComment
                fields = ("text", "post_owner")

            text = serializers.CharField()
            post_owner = PersonSerializer(source='blog_post.writer')

        class BlogPostSerializer(serializers.Serializer):
            title = serializers.CharField()
            comments = BlogPostCommentSerializer(source='blogpostcomment_set')

        serializer = BlogPostSerializer(instance=post)

        expected = {
            'title': u'Test blog post',
            'comments': [{
                'text': u'I love this blog post',
                'post_owner': {
                    "name": u"django",
                    "age": None
                }
            }]
        }

        self.assertEqual(serializer.data, expected)


class SerializerMethodFieldTests(TestCase):
    def setUp(self):

        class BoopSerializer(serializers.Serializer):
            beep = serializers.SerializerMethodField('get_beep')
            boop = serializers.Field()
            boop_count = serializers.SerializerMethodField('get_boop_count')

            def get_beep(self, obj):
                return 'hello!'

            def get_boop_count(self, obj):
                return len(obj.boop)

        self.serializer_class = BoopSerializer

    def test_serializer_method_field(self):

        class MyModel(object):
            boop = ['a', 'b', 'c']

        source_data = MyModel()

        serializer = self.serializer_class(source_data)

        expected = {
            'beep': u'hello!',
            'boop': [u'a', u'b', u'c'],
            'boop_count': 3,
        }

        self.assertEqual(serializer.data, expected)


# Test for issue #324
class BlankFieldTests(TestCase):
    def setUp(self):

        class BlankFieldModelSerializer(serializers.ModelSerializer):
            class Meta:
                model = BlankFieldModel

        class BlankFieldSerializer(serializers.Serializer):
            title = serializers.CharField(blank=True)

        class NotBlankFieldModelSerializer(serializers.ModelSerializer):
            class Meta:
                model = BasicModel

        class NotBlankFieldSerializer(serializers.Serializer):
            title = serializers.CharField()

        self.model_serializer_class = BlankFieldModelSerializer
        self.serializer_class = BlankFieldSerializer
        self.not_blank_model_serializer_class = NotBlankFieldModelSerializer
        self.not_blank_serializer_class = NotBlankFieldSerializer
        self.data = {'title': ''}

    def test_create_blank_field(self):
        serializer = self.serializer_class(data=self.data)
        self.assertEquals(serializer.is_valid(), True)

    def test_create_model_blank_field(self):
        serializer = self.model_serializer_class(data=self.data)
        self.assertEquals(serializer.is_valid(), True)

    def test_create_not_blank_field(self):
        """
        Test to ensure blank data in a field not marked as blank=True
        is considered invalid in a non-model serializer
        """
        serializer = self.not_blank_serializer_class(data=self.data)
        self.assertEquals(serializer.is_valid(), False)

    def test_create_model_not_blank_field(self):
        """
        Test to ensure blank data in a field not marked as blank=True
        is considered invalid in a model serializer
        """
        serializer = self.not_blank_model_serializer_class(data=self.data)
        self.assertEquals(serializer.is_valid(), False)


#test for issue #460
class SerializerPickleTests(TestCase):
    """
    Test pickleability of the output of Serializers
    """
    def test_pickle_simple_model_serializer_data(self):
        """
        Test simple serializer
        """
        pickle.dumps(PersonSerializer(Person(name="Methusela", age=969)).data)

    def test_pickle_inner_serializer(self):
        """
        Test pickling a serializer whose resulting .data (a SortedDictWithMetadata) will
        have unpickleable meta data--in order to make sure metadata doesn't get pulled into the pickle.
        See DictWithMetadata.__getstate__
        """
        class InnerPersonSerializer(serializers.ModelSerializer):
            class Meta:
                model = Person
                fields = ('name', 'age')
        pickle.dumps(InnerPersonSerializer(Person(name="Noah", age=950)).data)
