import datetime

from django.db import models
from django.test import TestCase

from rest_framework import serializers
from rest_framework.validators import UniqueValidator


def dedent(blocktext):
    return '\n'.join([line[12:] for line in blocktext.splitlines()[1:-1]])


# Tests for `UniqueValidator`
# ---------------------------

class UniquenessModel(models.Model):
    username = models.CharField(unique=True, max_length=100)


class UniquenessSerializer(serializers.ModelSerializer):
    class Meta:
        model = UniquenessModel


class RelatedModel(models.Model):
    user = models.OneToOneField(UniquenessModel, on_delete=models.CASCADE)
    email = models.CharField(unique=True, max_length=80)


class RelatedModelSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username',
        validators=[UniqueValidator(queryset=UniquenessModel.objects.all())])  # NOQA

    class Meta:
        model = RelatedModel
        fields = ('username', 'email')


class AnotherUniquenessModel(models.Model):
    code = models.IntegerField(unique=True)


class AnotherUniquenessSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnotherUniquenessModel


class TestUniquenessValidation(TestCase):
    def setUp(self):
        self.instance = UniquenessModel.objects.create(username='existing')

    def test_repr(self):
        serializer = UniquenessSerializer()
        expected = dedent("""
            UniquenessSerializer():
                id = IntegerField(label='ID', read_only=True)
                username = CharField(max_length=100, validators=[<UniqueValidator(queryset=UniquenessModel.objects.all())>])
        """)
        assert repr(serializer) == expected

    def test_is_not_unique(self):
        data = {'username': 'existing'}
        serializer = UniquenessSerializer(data=data)
        assert not serializer.is_valid()
        assert serializer.errors == {'username': ['UniquenessModel with this username already exists.']}

    def test_is_unique(self):
        data = {'username': 'other'}
        serializer = UniquenessSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data == {'username': 'other'}

    def test_updated_instance_excluded(self):
        data = {'username': 'existing'}
        serializer = UniquenessSerializer(self.instance, data=data)
        assert serializer.is_valid()
        assert serializer.validated_data == {'username': 'existing'}

    def test_doesnt_pollute_model(self):
        instance = AnotherUniquenessModel.objects.create(code='100')
        serializer = AnotherUniquenessSerializer(instance)
        self.assertEqual(
            AnotherUniquenessModel._meta.get_field('code').validators, [])

        # Accessing data shouldn't effect validators on the model
        serializer.data
        self.assertEqual(
            AnotherUniquenessModel._meta.get_field('code').validators, [])

    def test_related_model_is_unique(self):
        data = {'username': 'existing', 'email': 'new-email@example.com'}
        rs = RelatedModelSerializer(data=data)
        self.assertFalse(rs.is_valid())
        self.assertEqual(rs.errors,
                         {'username': ['This field must be unique.']})
        data = {'username': 'new-username', 'email': 'new-email@example.com'}
        rs = RelatedModelSerializer(data=data)
        self.assertTrue(rs.is_valid())


# Tests for `UniqueTogetherValidator`
# -----------------------------------

class UniquenessTogetherModel(models.Model):
    race_name = models.CharField(max_length=100)
    position = models.IntegerField()

    class Meta:
        unique_together = ('race_name', 'position')


class NullUniquenessTogetherModel(models.Model):
    """
    Used to ensure that null values are not included when checking
    unique_together constraints.

    Ignoring items which have a null in any of the validated fields is the same
    behavior that database backends will use when they have the
    unique_together constraint added.

    Example case: a null position could indicate a non-finisher in the race,
    there could be many non-finishers in a race, but all non-NULL
    values *should* be unique against the given `race_name`.
    """
    date_of_birth = models.DateField(null=True)  # Not part of the uniqueness constraint
    race_name = models.CharField(max_length=100)
    position = models.IntegerField(null=True)

    class Meta:
        unique_together = ('race_name', 'position')


class UniquenessTogetherSerializer(serializers.ModelSerializer):
    class Meta:
        model = UniquenessTogetherModel


class NullUniquenessTogetherSerializer(serializers.ModelSerializer):
    class Meta:
        model = NullUniquenessTogetherModel


class TestUniquenessTogetherValidation(TestCase):
    def setUp(self):
        self.instance = UniquenessTogetherModel.objects.create(
            race_name='example',
            position=1
        )
        UniquenessTogetherModel.objects.create(
            race_name='example',
            position=2
        )
        UniquenessTogetherModel.objects.create(
            race_name='other',
            position=1
        )

    def test_repr(self):
        serializer = UniquenessTogetherSerializer()
        expected = dedent("""
            UniquenessTogetherSerializer():
                id = IntegerField(label='ID', read_only=True)
                race_name = CharField(max_length=100, required=True)
                position = IntegerField(required=True)
                class Meta:
                    validators = [<UniqueTogetherValidator(queryset=UniquenessTogetherModel.objects.all(), fields=('race_name', 'position'))>]
        """)
        assert repr(serializer) == expected

    def test_is_not_unique_together(self):
        """
        Failing unique together validation should result in non field errors.
        """
        data = {'race_name': 'example', 'position': 2}
        serializer = UniquenessTogetherSerializer(data=data)
        assert not serializer.is_valid()
        assert serializer.errors == {
            'non_field_errors': [
                'The fields race_name, position must make a unique set.'
            ]
        }

    def test_is_unique_together(self):
        """
        In a unique together validation, one field may be non-unique
        so long as the set as a whole is unique.
        """
        data = {'race_name': 'other', 'position': 2}
        serializer = UniquenessTogetherSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data == {
            'race_name': 'other',
            'position': 2
        }

    def test_updated_instance_excluded_from_unique_together(self):
        """
        When performing an update, the existing instance does not count
        as a match against uniqueness.
        """
        data = {'race_name': 'example', 'position': 1}
        serializer = UniquenessTogetherSerializer(self.instance, data=data)
        assert serializer.is_valid()
        assert serializer.validated_data == {
            'race_name': 'example',
            'position': 1
        }

    def test_unique_together_is_required(self):
        """
        In a unique together validation, all fields are required.
        """
        data = {'position': 2}
        serializer = UniquenessTogetherSerializer(data=data, partial=True)
        assert not serializer.is_valid()
        assert serializer.errors == {
            'race_name': ['This field is required.']
        }

    def test_ignore_excluded_fields(self):
        """
        When model fields are not included in a serializer, then uniqueness
        validators should not be added for that field.
        """
        class ExcludedFieldSerializer(serializers.ModelSerializer):
            class Meta:
                model = UniquenessTogetherModel
                fields = ('id', 'race_name',)
        serializer = ExcludedFieldSerializer()
        expected = dedent("""
            ExcludedFieldSerializer():
                id = IntegerField(label='ID', read_only=True)
                race_name = CharField(max_length=100)
        """)
        assert repr(serializer) == expected

    def test_ignore_validation_for_null_fields(self):
        # None values that are on fields which are part of the uniqueness
        # constraint cause the instance to ignore uniqueness validation.
        NullUniquenessTogetherModel.objects.create(
            date_of_birth=datetime.date(2000, 1, 1),
            race_name='Paris Marathon',
            position=None
        )
        data = {
            'date': datetime.date(2000, 1, 1),
            'race_name': 'Paris Marathon',
            'position': None
        }
        serializer = NullUniquenessTogetherSerializer(data=data)
        assert serializer.is_valid()

    def test_do_not_ignore_validation_for_null_fields(self):
        # None values that are not on fields part of the uniqueness constraint
        # do not cause the instance to skip validation.
        NullUniquenessTogetherModel.objects.create(
            date_of_birth=datetime.date(2000, 1, 1),
            race_name='Paris Marathon',
            position=1
        )
        data = {'date': None, 'race_name': 'Paris Marathon', 'position': 1}
        serializer = NullUniquenessTogetherSerializer(data=data)
        assert not serializer.is_valid()


# Tests for `UniqueForDateValidator`
# ----------------------------------

class UniqueForDateModel(models.Model):
    slug = models.CharField(max_length=100, unique_for_date='published')
    published = models.DateField()


class UniqueForDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UniqueForDateModel


class TestUniquenessForDateValidation(TestCase):
    def setUp(self):
        self.instance = UniqueForDateModel.objects.create(
            slug='existing',
            published='2000-01-01'
        )

    def test_repr(self):
        serializer = UniqueForDateSerializer()
        expected = dedent("""
            UniqueForDateSerializer():
                id = IntegerField(label='ID', read_only=True)
                slug = CharField(max_length=100)
                published = DateField(required=True)
                class Meta:
                    validators = [<UniqueForDateValidator(queryset=UniqueForDateModel.objects.all(), field='slug', date_field='published')>]
        """)
        assert repr(serializer) == expected

    def test_is_not_unique_for_date(self):
        """
        Failing unique for date validation should result in field error.
        """
        data = {'slug': 'existing', 'published': '2000-01-01'}
        serializer = UniqueForDateSerializer(data=data)
        assert not serializer.is_valid()
        assert serializer.errors == {
            'slug': ['This field must be unique for the "published" date.']
        }

    def test_is_unique_for_date(self):
        """
        Passing unique for date validation.
        """
        data = {'slug': 'existing', 'published': '2000-01-02'}
        serializer = UniqueForDateSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data == {
            'slug': 'existing',
            'published': datetime.date(2000, 1, 2)
        }

    def test_updated_instance_excluded_from_unique_for_date(self):
        """
        When performing an update, the existing instance does not count
        as a match against unique_for_date.
        """
        data = {'slug': 'existing', 'published': '2000-01-01'}
        serializer = UniqueForDateSerializer(instance=self.instance, data=data)
        assert serializer.is_valid()
        assert serializer.validated_data == {
            'slug': 'existing',
            'published': datetime.date(2000, 1, 1)
        }


class HiddenFieldUniqueForDateModel(models.Model):
    slug = models.CharField(max_length=100, unique_for_date='published')
    published = models.DateTimeField(auto_now_add=True)


class TestHiddenFieldUniquenessForDateValidation(TestCase):
    def test_repr_date_field_not_included(self):
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = HiddenFieldUniqueForDateModel
                fields = ('id', 'slug')

        serializer = TestSerializer()
        expected = dedent("""
            TestSerializer():
                id = IntegerField(label='ID', read_only=True)
                slug = CharField(max_length=100)
                published = HiddenField(default=CreateOnlyDefault(<function now>))
                class Meta:
                    validators = [<UniqueForDateValidator(queryset=HiddenFieldUniqueForDateModel.objects.all(), field='slug', date_field='published')>]
        """)
        assert repr(serializer) == expected

    def test_repr_date_field_included(self):
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = HiddenFieldUniqueForDateModel
                fields = ('id', 'slug', 'published')

        serializer = TestSerializer()
        expected = dedent("""
            TestSerializer():
                id = IntegerField(label='ID', read_only=True)
                slug = CharField(max_length=100)
                published = DateTimeField(default=CreateOnlyDefault(<function now>), read_only=True)
                class Meta:
                    validators = [<UniqueForDateValidator(queryset=HiddenFieldUniqueForDateModel.objects.all(), field='slug', date_field='published')>]
        """)
        assert repr(serializer) == expected
