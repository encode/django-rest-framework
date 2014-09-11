"""
The `ModelSerializer` and `HyperlinkedModelSerializer` classes are essentially
shortcuts for automatically creating serializers based on a given model class.

These tests deal with ensuring that we correctly map the model fields onto
an appropriate set of serializer fields for each case.
"""
from django.db import models
from django.test import TestCase
from rest_framework import serializers


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


REGULAR_FIELDS_REPR = """
TestSerializer():
    auto_field = IntegerField(label='auto field', read_only=True)
    big_integer_field = IntegerField(label='big integer field')
    boolean_field = BooleanField(default=False, label='boolean field')
    char_field = CharField(label='char field', max_length=100)
    comma_seperated_integer_field = CharField(label='comma seperated integer field', max_length=100, validators=[<django.core.validators.RegexValidator object>])
    date_field = DateField(label='date field')
    datetime_field = DateTimeField(label='datetime field')
    decimal_field = DecimalField(decimal_places=1, label='decimal field', max_digits=3)
    email_field = EmailField(label='email field', max_length=100)
    float_field = FloatField(label='float field')
    integer_field = IntegerField(label='integer field')
    null_boolean_field = BooleanField(label='null boolean field', required=False)
    positive_integer_field = IntegerField(label='positive integer field')
    positive_small_integer_field = IntegerField(label='positive small integer field')
    slug_field = SlugField(label='slug field', max_length=100)
    small_integer_field = IntegerField(label='small integer field')
    text_field = CharField(label='text field')
    time_field = TimeField(label='time field')
    url_field = URLField(label='url field', max_length=100)
""".strip()


# Model for testing relational field mapping

class ForeignKeyTargetModel(models.Model):
    name = models.CharField(max_length=100)


class ManyToManyTargetModel(models.Model):
    name = models.CharField(max_length=100)


class OneToOneTargetModel(models.Model):
    name = models.CharField(max_length=100)


class RelationalModel(models.Model):
    foreign_key = models.ForeignKey(ForeignKeyTargetModel)
    many_to_many = models.ManyToManyField(ManyToManyTargetModel)
    one_to_one = models.OneToOneField(OneToOneTargetModel)


RELATIONAL_FLAT_REPR = """
TestSerializer():
    id = IntegerField(label='ID', read_only=True)
    foreign_key = PrimaryKeyRelatedField(label='foreign key', queryset=ForeignKeyTargetModel.objects.all())
    one_to_one = PrimaryKeyRelatedField(label='one to one', queryset=OneToOneTargetModel.objects.all())
    many_to_many = PrimaryKeyRelatedField(label='many to many', many=True, queryset=ManyToManyTargetModel.objects.all())
""".strip()


RELATIONAL_NESTED_REPR = """
TestSerializer():
    id = IntegerField(label='ID', read_only=True)
    foreign_key = NestedModelSerializer(read_only=True):
        id = IntegerField(label='ID', read_only=True)
        name = CharField(label='name', max_length=100)
    one_to_one = NestedModelSerializer(read_only=True):
        id = IntegerField(label='ID', read_only=True)
        name = CharField(label='name', max_length=100)
    many_to_many = NestedModelSerializer(many=True, read_only=True):
        id = IntegerField(label='ID', read_only=True)
        name = CharField(label='name', max_length=100)
""".strip()


HYPERLINKED_FLAT_REPR = """
TestSerializer():
    url = HyperlinkedIdentityField(view_name='relationalmodel-detail')
    foreign_key = HyperlinkedRelatedField(label='foreign key', queryset=ForeignKeyTargetModel.objects.all(), view_name='foreignkeytargetmodel-detail')
    one_to_one = HyperlinkedRelatedField(label='one to one', queryset=OneToOneTargetModel.objects.all(), view_name='onetoonetargetmodel-detail')
    many_to_many = HyperlinkedRelatedField(label='many to many', many=True, queryset=ManyToManyTargetModel.objects.all(), view_name='manytomanytargetmodel-detail')
""".strip()


HYPERLINKED_NESTED_REPR = """
TestSerializer():
    url = HyperlinkedIdentityField(view_name='relationalmodel-detail')
    foreign_key = NestedModelSerializer(read_only=True):
        id = IntegerField(label='ID', read_only=True)
        name = CharField(label='name', max_length=100)
    one_to_one = NestedModelSerializer(read_only=True):
        id = IntegerField(label='ID', read_only=True)
        name = CharField(label='name', max_length=100)
    many_to_many = NestedModelSerializer(many=True, read_only=True):
        id = IntegerField(label='ID', read_only=True)
        name = CharField(label='name', max_length=100)
""".strip()


class TestSerializerMappings(TestCase):
    maxDiff = 10000

    def test_regular_fields(self):
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = RegularFieldsModel
        self.assertEqual(repr(TestSerializer()), REGULAR_FIELDS_REPR)

    def test_flat_relational_fields(self):
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = RelationalModel
        self.assertEqual(repr(TestSerializer()), RELATIONAL_FLAT_REPR)

    def test_nested_relational_fields(self):
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = RelationalModel
                depth = 1
        self.assertEqual(repr(TestSerializer()), RELATIONAL_NESTED_REPR)

    def test_flat_hyperlinked_fields(self):
        class TestSerializer(serializers.HyperlinkedModelSerializer):
            class Meta:
                model = RelationalModel
        self.assertEqual(repr(TestSerializer()), HYPERLINKED_FLAT_REPR)

    def test_nested_hyperlinked_fields(self):
        class TestSerializer(serializers.HyperlinkedModelSerializer):
            class Meta:
                model = RelationalModel
                depth = 1
        self.assertEqual(repr(TestSerializer()), HYPERLINKED_NESTED_REPR)
