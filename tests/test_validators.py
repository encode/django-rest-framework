from django.db import models
from django.test import TestCase
from rest_framework import serializers
import datetime


def dedent(blocktext):
    return '\n'.join([line[12:] for line in blocktext.splitlines()[1:-1]])


# Tests for `UniqueValidator`
# ---------------------------

class UniquenessModel(models.Model):
    username = models.CharField(unique=True, max_length=100)


class UniquenessSerializer(serializers.ModelSerializer):
    class Meta:
        model = UniquenessModel


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
        assert serializer.errors == {'username': ['This field must be unique.']}

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


# Tests for `UniqueTogetherValidator`
# -----------------------------------

class UniquenessTogetherModel(models.Model):
    race_name = models.CharField(max_length=100)
    position = models.IntegerField()

    class Meta:
        unique_together = ('race_name', 'position')


class UniquenessTogetherSerializer(serializers.ModelSerializer):
    class Meta:
        model = UniquenessTogetherModel


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
                race_name = CharField(max_length=100)
                position = IntegerField()
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

    def test_ignore_excluded_fields(self):
        """
        When model fields are not included in a serializer, then uniqueness
        validtors should not be added for that field.
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
