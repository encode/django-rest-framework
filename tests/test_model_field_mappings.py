"""
The `ModelSerializer` and `HyperlinkedModelSerializer` classes are essentially
shortcuts for automatically creating serializers based on a given model class.

These tests deal with ensuring that we correctly map the model fields onto
an appropriate set of serializer fields for each case.
"""
from django.db import models
from django.test import TestCase
from rest_framework import serializers


def dedent(blocktext):
    return '\n'.join([line[12:] for line in blocktext.splitlines()[1:-1]])


# Models for testing regular field mapping

class RegularFieldsModel(models.Model):
    auto_field = models.AutoField(primary_key=True)
    big_integer_field = models.BigIntegerField()
    boolean_field = models.BooleanField(default=False)
    char_field = models.CharField(max_length=100)
    comma_seperated_integer_field = models.CommaSeparatedIntegerField(max_length=100)
    date_field = models.DateField()
    datetime_field = models.DateTimeField()
    decimal_field = models.DecimalField(max_digits=3, decimal_places=1)
    email_field = models.EmailField(max_length=100)
    float_field = models.FloatField()
    integer_field = models.IntegerField()
    null_boolean_field = models.NullBooleanField()
    positive_integer_field = models.PositiveIntegerField()
    positive_small_integer_field = models.PositiveSmallIntegerField()
    slug_field = models.SlugField(max_length=100)
    small_integer_field = models.SmallIntegerField()
    text_field = models.TextField()
    time_field = models.TimeField()
    url_field = models.URLField(max_length=100)


class TestRegularFieldMappings(TestCase):
    def test_regular_fields(self):
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = RegularFieldsModel

        expected = dedent("""
            TestSerializer():
                auto_field = IntegerField(read_only=True)
                big_integer_field = IntegerField()
                boolean_field = BooleanField(default=False)
                char_field = CharField(max_length=100)
                comma_seperated_integer_field = CharField(max_length=100, validators=[<django.core.validators.RegexValidator object>])
                date_field = DateField()
                datetime_field = DateTimeField()
                decimal_field = DecimalField(decimal_places=1, max_digits=3)
                email_field = EmailField(max_length=100)
                float_field = FloatField()
                integer_field = IntegerField()
                null_boolean_field = BooleanField(required=False)
                positive_integer_field = IntegerField()
                positive_small_integer_field = IntegerField()
                slug_field = SlugField(max_length=100)
                small_integer_field = IntegerField()
                text_field = CharField()
                time_field = TimeField()
                url_field = URLField(max_length=100)
        """)

        self.assertEqual(repr(TestSerializer()), expected)


# Model for testing relational field mapping

class ForeignKeyTargetModel(models.Model):
    name = models.CharField(max_length=100)


class ManyToManyTargetModel(models.Model):
    name = models.CharField(max_length=100)


class OneToOneTargetModel(models.Model):
    name = models.CharField(max_length=100)


class RelationalModel(models.Model):
    foreign_key = models.ForeignKey(ForeignKeyTargetModel, related_name='reverse_foreign_key')
    many_to_many = models.ManyToManyField(ManyToManyTargetModel, related_name='reverse_many_to_many')
    one_to_one = models.OneToOneField(OneToOneTargetModel, related_name='reverse_one_to_one')


class TestRelationalFieldMappings(TestCase):
    def test_flat_relational_fields(self):
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = RelationalModel

        expected = dedent("""
            TestSerializer():
                id = IntegerField(label='ID', read_only=True)
                foreign_key = PrimaryKeyRelatedField(queryset=ForeignKeyTargetModel.objects.all())
                one_to_one = PrimaryKeyRelatedField(queryset=OneToOneTargetModel.objects.all())
                many_to_many = PrimaryKeyRelatedField(many=True, queryset=ManyToManyTargetModel.objects.all())
        """)
        self.assertEqual(repr(TestSerializer()), expected)

    def test_nested_relational_fields(self):
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = RelationalModel
                depth = 1

        expected = dedent("""
            TestSerializer():
                id = IntegerField(label='ID', read_only=True)
                foreign_key = NestedModelSerializer(read_only=True):
                    id = IntegerField(label='ID', read_only=True)
                    name = CharField(max_length=100)
                one_to_one = NestedModelSerializer(read_only=True):
                    id = IntegerField(label='ID', read_only=True)
                    name = CharField(max_length=100)
                many_to_many = NestedModelSerializer(many=True, read_only=True):
                    id = IntegerField(label='ID', read_only=True)
                    name = CharField(max_length=100)
        """)
        self.assertEqual(repr(TestSerializer()), expected)

    def test_flat_hyperlinked_fields(self):
        class TestSerializer(serializers.HyperlinkedModelSerializer):
            class Meta:
                model = RelationalModel

        expected = dedent("""
            TestSerializer():
                url = HyperlinkedIdentityField(view_name='relationalmodel-detail')
                foreign_key = HyperlinkedRelatedField(queryset=ForeignKeyTargetModel.objects.all(), view_name='foreignkeytargetmodel-detail')
                one_to_one = HyperlinkedRelatedField(queryset=OneToOneTargetModel.objects.all(), view_name='onetoonetargetmodel-detail')
                many_to_many = HyperlinkedRelatedField(many=True, queryset=ManyToManyTargetModel.objects.all(), view_name='manytomanytargetmodel-detail')
        """)
        self.assertEqual(repr(TestSerializer()), expected)

    def test_nested_hyperlinked_fields(self):
        class TestSerializer(serializers.HyperlinkedModelSerializer):
            class Meta:
                model = RelationalModel
                depth = 1

        expected = dedent("""
            TestSerializer():
                url = HyperlinkedIdentityField(view_name='relationalmodel-detail')
                foreign_key = NestedModelSerializer(read_only=True):
                    url = HyperlinkedIdentityField(view_name='foreignkeytargetmodel-detail')
                    name = CharField(max_length=100)
                one_to_one = NestedModelSerializer(read_only=True):
                    url = HyperlinkedIdentityField(view_name='onetoonetargetmodel-detail')
                    name = CharField(max_length=100)
                many_to_many = NestedModelSerializer(many=True, read_only=True):
                    url = HyperlinkedIdentityField(view_name='manytomanytargetmodel-detail')
                    name = CharField(max_length=100)
        """)
        self.assertEqual(repr(TestSerializer()), expected)

    def test_flat_reverse_foreign_key(self):
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = ForeignKeyTargetModel
                fields = ('id', 'name', 'reverse_foreign_key')

        expected = dedent("""
            TestSerializer():
                id = IntegerField(label='ID', read_only=True)
                name = CharField(max_length=100)
                reverse_foreign_key = PrimaryKeyRelatedField(many=True, queryset=RelationalModel.objects.all())
        """)
        self.assertEqual(repr(TestSerializer()), expected)

    def test_flat_reverse_one_to_one(self):
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = OneToOneTargetModel
                fields = ('id', 'name', 'reverse_one_to_one')

        expected = dedent("""
            TestSerializer():
                id = IntegerField(label='ID', read_only=True)
                name = CharField(max_length=100)
                reverse_one_to_one = PrimaryKeyRelatedField(queryset=RelationalModel.objects.all())
        """)
        self.assertEqual(repr(TestSerializer()), expected)

    def test_flat_reverse_many_to_many(self):
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = ManyToManyTargetModel
                fields = ('id', 'name', 'reverse_many_to_many')

        expected = dedent("""
            TestSerializer():
                id = IntegerField(label='ID', read_only=True)
                name = CharField(max_length=100)
                reverse_many_to_many = PrimaryKeyRelatedField(many=True, queryset=RelationalModel.objects.all())
        """)
        self.assertEqual(repr(TestSerializer()), expected)
