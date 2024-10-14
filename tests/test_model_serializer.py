"""
The `ModelSerializer` and `HyperlinkedModelSerializer` classes are essentially
shortcuts for automatically creating serializers based on a given model class.

These tests deal with ensuring that we correctly map the model fields onto
an appropriate set of serializer fields for each case.
"""
import datetime
import decimal
import json  # noqa
import re
import sys
import tempfile

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.core.serializers.json import DjangoJSONEncoder
from django.core.validators import (
    MaxValueValidator, MinLengthValidator, MinValueValidator
)
from django.db import models
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.test import TestCase

from rest_framework import serializers
from rest_framework.compat import postgres_fields

from .models import NestedForeignKeySource


def dedent(blocktext):
    return '\n'.join([line[12:] for line in blocktext.splitlines()[1:-1]])


# Tests for regular field mappings.
# ---------------------------------

class CustomField(models.Field):
    """
    A custom model field simply for testing purposes.
    """
    pass


class OneFieldModel(models.Model):
    char_field = models.CharField(max_length=100)


class RegularFieldsModel(models.Model):
    """
    A model class for testing regular flat fields.
    """
    auto_field = models.AutoField(primary_key=True)
    big_integer_field = models.BigIntegerField()
    boolean_field = models.BooleanField(default=False)
    char_field = models.CharField(max_length=100)
    comma_separated_integer_field = models.CommaSeparatedIntegerField(max_length=100)
    date_field = models.DateField()
    datetime_field = models.DateTimeField()
    decimal_field = models.DecimalField(max_digits=3, decimal_places=1)
    email_field = models.EmailField(max_length=100)
    float_field = models.FloatField()
    integer_field = models.IntegerField()
    null_boolean_field = models.BooleanField(null=True, default=False)
    positive_integer_field = models.PositiveIntegerField()
    positive_small_integer_field = models.PositiveSmallIntegerField()
    slug_field = models.SlugField(max_length=100)
    small_integer_field = models.SmallIntegerField()
    text_field = models.TextField(max_length=100)
    file_field = models.FileField(max_length=100)
    time_field = models.TimeField()
    url_field = models.URLField(max_length=100)
    custom_field = CustomField()
    file_path_field = models.FilePathField(path=tempfile.gettempdir())

    def method(self):
        return 'method'


COLOR_CHOICES = (('red', 'Red'), ('blue', 'Blue'), ('green', 'Green'))
DECIMAL_CHOICES = (('low', decimal.Decimal('0.1')), ('medium', decimal.Decimal('0.5')), ('high', decimal.Decimal('0.9')))


class FieldOptionsModel(models.Model):
    value_limit_field = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    length_limit_field = models.CharField(validators=[MinLengthValidator(3)], max_length=12)
    blank_field = models.CharField(blank=True, max_length=10)
    null_field = models.IntegerField(null=True)
    default_field = models.IntegerField(default=0)
    descriptive_field = models.IntegerField(help_text='Some help text', verbose_name='A label')
    choices_field = models.CharField(max_length=100, choices=COLOR_CHOICES)
    text_choices_field = models.TextField(choices=COLOR_CHOICES)


class ChoicesModel(models.Model):
    choices_field_with_nonstandard_args = models.DecimalField(max_digits=3, decimal_places=1, choices=DECIMAL_CHOICES, verbose_name='A label')


class Issue3674ParentModel(models.Model):
    title = models.CharField(max_length=64)


class Issue3674ChildModel(models.Model):
    parent = models.ForeignKey(Issue3674ParentModel, related_name='children', on_delete=models.CASCADE)
    value = models.CharField(primary_key=True, max_length=64)


class UniqueChoiceModel(models.Model):
    CHOICES = (
        ('choice1', 'choice 1'),
        ('choice2', 'choice 1'),
    )

    name = models.CharField(max_length=254, unique=True, choices=CHOICES)


class TestModelSerializer(TestCase):
    def test_create_method(self):
        class TestSerializer(serializers.ModelSerializer):
            non_model_field = serializers.CharField()

            class Meta:
                model = OneFieldModel
                fields = ('char_field', 'non_model_field')

        serializer = TestSerializer(data={
            'char_field': 'foo',
            'non_model_field': 'bar',
        })
        serializer.is_valid()

        msginitial = 'Got a `TypeError` when calling `OneFieldModel.objects.create()`.'
        with self.assertRaisesMessage(TypeError, msginitial):
            serializer.save()

    def test_abstract_model(self):
        """
        Test that trying to use ModelSerializer with Abstract Models
        throws a ValueError exception.
        """
        class AbstractModel(models.Model):
            afield = models.CharField(max_length=255)

            class Meta:
                abstract = True

        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = AbstractModel
                fields = ('afield',)

        serializer = TestSerializer(data={
            'afield': 'foo',
        })

        msginitial = 'Cannot use ModelSerializer with Abstract Models.'
        with self.assertRaisesMessage(ValueError, msginitial):
            serializer.is_valid()


class TestRegularFieldMappings(TestCase):
    def test_regular_fields(self):
        """
        Model fields should map to their equivalent serializer fields.
        """
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = RegularFieldsModel
                fields = '__all__'

        expected = dedent(r"""
            TestSerializer\(\):
                auto_field = IntegerField\(read_only=True\)
                big_integer_field = IntegerField\(.*\)
                boolean_field = BooleanField\(required=False\)
                char_field = CharField\(max_length=100\)
                comma_separated_integer_field = CharField\(max_length=100, validators=\[<django.core.validators.RegexValidator object>\]\)
                date_field = DateField\(\)
                datetime_field = DateTimeField\(\)
                decimal_field = DecimalField\(decimal_places=1, max_digits=3\)
                email_field = EmailField\(max_length=100\)
                float_field = FloatField\(\)
                integer_field = IntegerField\(.*\)
                null_boolean_field = BooleanField\(allow_null=True, required=False\)
                positive_integer_field = IntegerField\(.*\)
                positive_small_integer_field = IntegerField\(.*\)
                slug_field = SlugField\(allow_unicode=False, max_length=100\)
                small_integer_field = IntegerField\(.*\)
                text_field = CharField\(max_length=100, style={'base_template': 'textarea.html'}\)
                file_field = FileField\(max_length=100\)
                time_field = TimeField\(\)
                url_field = URLField\(max_length=100\)
                custom_field = ModelField\(model_field=<tests.test_model_serializer.CustomField: custom_field>\)
                file_path_field = FilePathField\(path=%r\)
        """ % tempfile.gettempdir())
        assert re.search(expected, repr(TestSerializer())) is not None

    def test_field_options(self):
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = FieldOptionsModel
                fields = '__all__'

        expected = dedent(r"""
            TestSerializer\(\):
                id = IntegerField\(label='ID', read_only=True\)
                value_limit_field = IntegerField\(max_value=10, min_value=1\)
                length_limit_field = CharField\(max_length=12, min_length=3\)
                blank_field = CharField\(allow_blank=True, max_length=10, required=False\)
                null_field = IntegerField\(allow_null=True,.*required=False\)
                default_field = IntegerField\(.*required=False\)
                descriptive_field = IntegerField\(help_text='Some help text', label='A label'.*\)
                choices_field = ChoiceField\(choices=(?:\[|\()\('red', 'Red'\), \('blue', 'Blue'\), \('green', 'Green'\)(?:\]|\))\)
                text_choices_field = ChoiceField\(choices=(?:\[|\()\('red', 'Red'\), \('blue', 'Blue'\), \('green', 'Green'\)(?:\]|\))\)
        """)
        assert re.search(expected, repr(TestSerializer())) is not None

    def test_nullable_boolean_field_choices(self):
        class NullableBooleanChoicesModel(models.Model):
            CHECKLIST_OPTIONS = (
                (None, 'Unknown'),
                (True, 'Yes'),
                (False, 'No'),
            )

            field = models.BooleanField(null=True, choices=CHECKLIST_OPTIONS)

        class NullableBooleanChoicesSerializer(serializers.ModelSerializer):
            class Meta:
                model = NullableBooleanChoicesModel
                fields = ['field']

        serializer = NullableBooleanChoicesSerializer(data=dict(
            field=None,
        ))
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.errors, {})

    def test_method_field(self):
        """
        Properties and methods on the model should be allowed as `Meta.fields`
        values, and should map to `ReadOnlyField`.
        """
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = RegularFieldsModel
                fields = ('auto_field', 'method')

        expected = dedent("""
            TestSerializer():
                auto_field = IntegerField(read_only=True)
                method = ReadOnlyField()
        """)
        self.assertEqual(repr(TestSerializer()), expected)

    def test_pk_fields(self):
        """
        Both `pk` and the actual primary key name are valid in `Meta.fields`.
        """
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = RegularFieldsModel
                fields = ('pk', 'auto_field')

        expected = dedent("""
            TestSerializer():
                pk = IntegerField(label='Auto field', read_only=True)
                auto_field = IntegerField(read_only=True)
        """)
        self.assertEqual(repr(TestSerializer()), expected)

    def test_extra_field_kwargs(self):
        """
        Ensure `extra_kwargs` are passed to generated fields.
        """
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = RegularFieldsModel
                fields = ('auto_field', 'char_field')
                extra_kwargs = {'char_field': {'default': 'extra'}}

        expected = dedent("""
            TestSerializer():
                auto_field = IntegerField(read_only=True)
                char_field = CharField(default='extra', max_length=100)
        """)
        self.assertEqual(repr(TestSerializer()), expected)

    def test_extra_field_kwargs_required(self):
        """
        Ensure `extra_kwargs` are passed to generated fields.
        """
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = RegularFieldsModel
                fields = ('auto_field', 'char_field')
                extra_kwargs = {'auto_field': {'required': False, 'read_only': False}}

        expected = dedent("""
            TestSerializer():
                auto_field = IntegerField(read_only=False, required=False)
                char_field = CharField(max_length=100)
        """)
        self.assertEqual(repr(TestSerializer()), expected)

    def test_invalid_field(self):
        """
        Field names that do not map to a model field or relationship should
        raise a configuration error.
        """
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = RegularFieldsModel
                fields = ('auto_field', 'invalid')

        expected = 'Field name `invalid` is not valid for model `RegularFieldsModel` ' \
                   'in `tests.test_model_serializer.TestSerializer`.'
        with self.assertRaisesMessage(ImproperlyConfigured, expected):
            TestSerializer().fields

    def test_missing_field(self):
        """
        Fields that have been declared on the serializer class must be included
        in the `Meta.fields` if it exists.
        """
        class TestSerializer(serializers.ModelSerializer):
            missing = serializers.ReadOnlyField()

            class Meta:
                model = RegularFieldsModel
                fields = ('auto_field',)

        expected = (
            "The field 'missing' was declared on serializer TestSerializer, "
            "but has not been included in the 'fields' option."
        )
        with self.assertRaisesMessage(AssertionError, expected):
            TestSerializer().fields

    def test_missing_superclass_field(self):
        """
        Fields that have been declared on a parent of the serializer class may
        be excluded from the `Meta.fields` option.
        """
        class TestSerializer(serializers.ModelSerializer):
            missing = serializers.ReadOnlyField()

        class ChildSerializer(TestSerializer):
            class Meta:
                model = RegularFieldsModel
                fields = ('auto_field',)

        ChildSerializer().fields

    def test_choices_with_nonstandard_args(self):
        class ExampleSerializer(serializers.ModelSerializer):
            class Meta:
                model = ChoicesModel
                fields = '__all__'

        ExampleSerializer()


class TestDurationFieldMapping(TestCase):
    def test_duration_field(self):
        class DurationFieldModel(models.Model):
            """
            A model that defines DurationField.
            """
            duration_field = models.DurationField()

        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = DurationFieldModel
                fields = '__all__'

        expected = dedent("""
            TestSerializer():
                id = IntegerField(label='ID', read_only=True)
                duration_field = DurationField()
        """)
        self.assertEqual(repr(TestSerializer()), expected)

    def test_duration_field_with_validators(self):
        class ValidatedDurationFieldModel(models.Model):
            """
            A model that defines DurationField with validators.
            """
            duration_field = models.DurationField(
                validators=[MinValueValidator(datetime.timedelta(days=1)), MaxValueValidator(datetime.timedelta(days=3))]
            )

        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = ValidatedDurationFieldModel
                fields = '__all__'

        expected = dedent("""
            TestSerializer():
                id = IntegerField(label='ID', read_only=True)
                duration_field = DurationField(max_value=datetime.timedelta(3), min_value=datetime.timedelta(1))
        """) if sys.version_info < (3, 7) else dedent("""
            TestSerializer():
                id = IntegerField(label='ID', read_only=True)
                duration_field = DurationField(max_value=datetime.timedelta(days=3), min_value=datetime.timedelta(days=1))
        """)
        self.assertEqual(repr(TestSerializer()), expected)


class TestGenericIPAddressFieldValidation(TestCase):
    def test_ip_address_validation(self):
        class IPAddressFieldModel(models.Model):
            address = models.GenericIPAddressField()

        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = IPAddressFieldModel
                fields = '__all__'

        s = TestSerializer(data={'address': 'not an ip address'})
        self.assertFalse(s.is_valid())
        self.assertEqual(1, len(s.errors['address']),
                         'Unexpected number of validation errors: '
                         '{}'.format(s.errors))


@pytest.mark.skipif('not postgres_fields')
class TestPosgresFieldsMapping(TestCase):
    def test_hstore_field(self):
        class HStoreFieldModel(models.Model):
            hstore_field = postgres_fields.HStoreField()

        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = HStoreFieldModel
                fields = ['hstore_field']

        expected = dedent("""
            TestSerializer():
                hstore_field = HStoreField()
        """)
        self.assertEqual(repr(TestSerializer()), expected)

    def test_array_field(self):
        class ArrayFieldModel(models.Model):
            array_field = postgres_fields.ArrayField(base_field=models.CharField())
            array_field_with_blank = postgres_fields.ArrayField(blank=True, base_field=models.CharField())

        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = ArrayFieldModel
                fields = ['array_field', 'array_field_with_blank']

        expected = dedent("""
            TestSerializer():
                array_field = ListField(allow_empty=False, child=CharField(label='Array field'))
                array_field_with_blank = ListField(child=CharField(label='Array field with blank'), required=False)
        """)
        self.assertEqual(repr(TestSerializer()), expected)

    @pytest.mark.skipif(hasattr(models, 'JSONField'), reason='has models.JSONField')
    def test_json_field(self):
        class JSONFieldModel(models.Model):
            json_field = postgres_fields.JSONField()
            json_field_with_encoder = postgres_fields.JSONField(encoder=DjangoJSONEncoder)

        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = JSONFieldModel
                fields = ['json_field', 'json_field_with_encoder']

        expected = dedent("""
            TestSerializer():
                json_field = JSONField(encoder=None, style={'base_template': 'textarea.html'})
                json_field_with_encoder = JSONField(encoder=<class 'django.core.serializers.json.DjangoJSONEncoder'>, style={'base_template': 'textarea.html'})
        """)
        self.assertEqual(repr(TestSerializer()), expected)


class CustomJSONDecoder(json.JSONDecoder):
    pass


@pytest.mark.skipif(not hasattr(models, 'JSONField'), reason='no models.JSONField')
class TestDjangoJSONFieldMapping(TestCase):
    def test_json_field(self):
        class JSONFieldModel(models.Model):
            json_field = models.JSONField()
            json_field_with_encoder = models.JSONField(encoder=DjangoJSONEncoder, decoder=CustomJSONDecoder)

        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = JSONFieldModel
                fields = ['json_field', 'json_field_with_encoder']

        expected = dedent("""
            TestSerializer():
                json_field = JSONField(decoder=None, encoder=None, style={'base_template': 'textarea.html'})
                json_field_with_encoder = JSONField(decoder=<class 'tests.test_model_serializer.CustomJSONDecoder'>, encoder=<class 'django.core.serializers.json.DjangoJSONEncoder'>, style={'base_template': 'textarea.html'})
        """)
        self.assertEqual(repr(TestSerializer()), expected)


# Tests for relational field mappings.
# ------------------------------------

class ForeignKeyTargetModel(models.Model):
    name = models.CharField(max_length=100)


class ManyToManyTargetModel(models.Model):
    name = models.CharField(max_length=100)


class OneToOneTargetModel(models.Model):
    name = models.CharField(max_length=100)


class ThroughTargetModel(models.Model):
    name = models.CharField(max_length=100)


class Supplementary(models.Model):
    extra = models.IntegerField()
    forwards = models.ForeignKey('ThroughTargetModel', on_delete=models.CASCADE)
    backwards = models.ForeignKey('RelationalModel', on_delete=models.CASCADE)


class RelationalModel(models.Model):
    foreign_key = models.ForeignKey(ForeignKeyTargetModel, related_name='reverse_foreign_key', on_delete=models.CASCADE)
    many_to_many = models.ManyToManyField(ManyToManyTargetModel, related_name='reverse_many_to_many')
    one_to_one = models.OneToOneField(OneToOneTargetModel, related_name='reverse_one_to_one', on_delete=models.CASCADE)
    through = models.ManyToManyField(ThroughTargetModel, through=Supplementary, related_name='reverse_through')


class UniqueTogetherModel(models.Model):
    foreign_key = models.ForeignKey(ForeignKeyTargetModel, related_name='unique_foreign_key', on_delete=models.CASCADE)
    one_to_one = models.OneToOneField(OneToOneTargetModel, related_name='unique_one_to_one', on_delete=models.CASCADE)

    class Meta:
        unique_together = ("foreign_key", "one_to_one")


class TestRelationalFieldMappings(TestCase):
    def test_pk_relations(self):
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = RelationalModel
                fields = '__all__'

        expected = dedent("""
            TestSerializer():
                id = IntegerField(label='ID', read_only=True)
                foreign_key = PrimaryKeyRelatedField(queryset=ForeignKeyTargetModel.objects.all())
                one_to_one = PrimaryKeyRelatedField(queryset=OneToOneTargetModel.objects.all(), validators=[<UniqueValidator(queryset=RelationalModel.objects.all())>])
                many_to_many = PrimaryKeyRelatedField(allow_empty=False, many=True, queryset=ManyToManyTargetModel.objects.all())
                through = PrimaryKeyRelatedField(many=True, read_only=True)
        """)
        self.assertEqual(repr(TestSerializer()), expected)

    def test_nested_relations(self):
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = RelationalModel
                depth = 1
                fields = '__all__'

        expected = dedent("""
            TestSerializer():
                id = IntegerField(label='ID', read_only=True)
                foreign_key = NestedSerializer(read_only=True):
                    id = IntegerField(label='ID', read_only=True)
                    name = CharField(max_length=100)
                one_to_one = NestedSerializer(read_only=True):
                    id = IntegerField(label='ID', read_only=True)
                    name = CharField(max_length=100)
                many_to_many = NestedSerializer(many=True, read_only=True):
                    id = IntegerField(label='ID', read_only=True)
                    name = CharField(max_length=100)
                through = NestedSerializer(many=True, read_only=True):
                    id = IntegerField(label='ID', read_only=True)
                    name = CharField(max_length=100)
        """)
        self.assertEqual(repr(TestSerializer()), expected)

    def test_hyperlinked_relations(self):
        class TestSerializer(serializers.HyperlinkedModelSerializer):
            class Meta:
                model = RelationalModel
                fields = '__all__'

        expected = dedent("""
            TestSerializer():
                url = HyperlinkedIdentityField(view_name='relationalmodel-detail')
                foreign_key = HyperlinkedRelatedField(queryset=ForeignKeyTargetModel.objects.all(), view_name='foreignkeytargetmodel-detail')
                one_to_one = HyperlinkedRelatedField(queryset=OneToOneTargetModel.objects.all(), validators=[<UniqueValidator(queryset=RelationalModel.objects.all())>], view_name='onetoonetargetmodel-detail')
                many_to_many = HyperlinkedRelatedField(allow_empty=False, many=True, queryset=ManyToManyTargetModel.objects.all(), view_name='manytomanytargetmodel-detail')
                through = HyperlinkedRelatedField(many=True, read_only=True, view_name='throughtargetmodel-detail')
        """)
        self.assertEqual(repr(TestSerializer()), expected)

    def test_nested_hyperlinked_relations(self):
        class TestSerializer(serializers.HyperlinkedModelSerializer):
            class Meta:
                model = RelationalModel
                depth = 1
                fields = '__all__'

        expected = dedent("""
            TestSerializer():
                url = HyperlinkedIdentityField(view_name='relationalmodel-detail')
                foreign_key = NestedSerializer(read_only=True):
                    url = HyperlinkedIdentityField(view_name='foreignkeytargetmodel-detail')
                    name = CharField(max_length=100)
                one_to_one = NestedSerializer(read_only=True):
                    url = HyperlinkedIdentityField(view_name='onetoonetargetmodel-detail')
                    name = CharField(max_length=100)
                many_to_many = NestedSerializer(many=True, read_only=True):
                    url = HyperlinkedIdentityField(view_name='manytomanytargetmodel-detail')
                    name = CharField(max_length=100)
                through = NestedSerializer(many=True, read_only=True):
                    url = HyperlinkedIdentityField(view_name='throughtargetmodel-detail')
                    name = CharField(max_length=100)
        """)
        self.assertEqual(repr(TestSerializer()), expected)

    def test_nested_hyperlinked_relations_starred_source(self):
        class TestSerializer(serializers.HyperlinkedModelSerializer):
            class Meta:
                model = RelationalModel
                depth = 1
                fields = '__all__'

                extra_kwargs = {
                    'url': {
                        'source': '*',
                    }}

        expected = dedent("""
            TestSerializer():
                url = HyperlinkedIdentityField(source='*', view_name='relationalmodel-detail')
                foreign_key = NestedSerializer(read_only=True):
                    url = HyperlinkedIdentityField(view_name='foreignkeytargetmodel-detail')
                    name = CharField(max_length=100)
                one_to_one = NestedSerializer(read_only=True):
                    url = HyperlinkedIdentityField(view_name='onetoonetargetmodel-detail')
                    name = CharField(max_length=100)
                many_to_many = NestedSerializer(many=True, read_only=True):
                    url = HyperlinkedIdentityField(view_name='manytomanytargetmodel-detail')
                    name = CharField(max_length=100)
                through = NestedSerializer(many=True, read_only=True):
                    url = HyperlinkedIdentityField(view_name='throughtargetmodel-detail')
                    name = CharField(max_length=100)
        """)
        self.maxDiff = None
        self.assertEqual(repr(TestSerializer()), expected)

    def test_nested_unique_together_relations(self):
        class TestSerializer(serializers.HyperlinkedModelSerializer):
            class Meta:
                model = UniqueTogetherModel
                depth = 1
                fields = '__all__'

        expected = dedent("""
            TestSerializer():
                url = HyperlinkedIdentityField(view_name='uniquetogethermodel-detail')
                foreign_key = NestedSerializer(read_only=True):
                    url = HyperlinkedIdentityField(view_name='foreignkeytargetmodel-detail')
                    name = CharField(max_length=100)
                one_to_one = NestedSerializer(read_only=True):
                    url = HyperlinkedIdentityField(view_name='onetoonetargetmodel-detail')
                    name = CharField(max_length=100)
        """)
        self.assertEqual(repr(TestSerializer()), expected)

    def test_pk_reverse_foreign_key(self):
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

    def test_pk_reverse_one_to_one(self):
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

    def test_pk_reverse_many_to_many(self):
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

    def test_pk_reverse_through(self):
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = ThroughTargetModel
                fields = ('id', 'name', 'reverse_through')

        expected = dedent("""
            TestSerializer():
                id = IntegerField(label='ID', read_only=True)
                name = CharField(max_length=100)
                reverse_through = PrimaryKeyRelatedField(many=True, read_only=True)
        """)
        self.assertEqual(repr(TestSerializer()), expected)


class DisplayValueTargetModel(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return '%s Color' % (self.name)


class DisplayValueModel(models.Model):
    color = models.ForeignKey(DisplayValueTargetModel, on_delete=models.CASCADE)


class TestRelationalFieldDisplayValue(TestCase):
    def setUp(self):
        DisplayValueTargetModel.objects.bulk_create([
            DisplayValueTargetModel(name='Red'),
            DisplayValueTargetModel(name='Yellow'),
            DisplayValueTargetModel(name='Green'),
        ])

    def test_default_display_value(self):
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = DisplayValueModel
                fields = '__all__'

        serializer = TestSerializer()
        expected = {1: 'Red Color', 2: 'Yellow Color', 3: 'Green Color'}
        self.assertEqual(serializer.fields['color'].choices, expected)

    def test_custom_display_value(self):
        class TestField(serializers.PrimaryKeyRelatedField):
            def display_value(self, instance):
                return 'My %s Color' % (instance.name)

        class TestSerializer(serializers.ModelSerializer):
            color = TestField(queryset=DisplayValueTargetModel.objects.all())

            class Meta:
                model = DisplayValueModel
                fields = '__all__'

        serializer = TestSerializer()
        expected = {1: 'My Red Color', 2: 'My Yellow Color', 3: 'My Green Color'}
        self.assertEqual(serializer.fields['color'].choices, expected)


class TestIntegration(TestCase):
    def setUp(self):
        self.foreign_key_target = ForeignKeyTargetModel.objects.create(
            name='foreign_key'
        )
        self.one_to_one_target = OneToOneTargetModel.objects.create(
            name='one_to_one'
        )
        self.many_to_many_targets = [
            ManyToManyTargetModel.objects.create(
                name='many_to_many (%d)' % idx
            ) for idx in range(3)
        ]
        self.instance = RelationalModel.objects.create(
            foreign_key=self.foreign_key_target,
            one_to_one=self.one_to_one_target,
        )
        self.instance.many_to_many.set(self.many_to_many_targets)

    def test_pk_retrival(self):
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = RelationalModel
                fields = '__all__'

        serializer = TestSerializer(self.instance)
        expected = {
            'id': self.instance.pk,
            'foreign_key': self.foreign_key_target.pk,
            'one_to_one': self.one_to_one_target.pk,
            'many_to_many': [item.pk for item in self.many_to_many_targets],
            'through': []
        }
        self.assertEqual(serializer.data, expected)

    def test_pk_create(self):
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = RelationalModel
                fields = '__all__'

        new_foreign_key = ForeignKeyTargetModel.objects.create(
            name='foreign_key'
        )
        new_one_to_one = OneToOneTargetModel.objects.create(
            name='one_to_one'
        )
        new_many_to_many = [
            ManyToManyTargetModel.objects.create(
                name='new many_to_many (%d)' % idx
            ) for idx in range(3)
        ]
        data = {
            'foreign_key': new_foreign_key.pk,
            'one_to_one': new_one_to_one.pk,
            'many_to_many': [item.pk for item in new_many_to_many],
        }

        # Serializer should validate okay.
        serializer = TestSerializer(data=data)
        assert serializer.is_valid()

        # Creating the instance, relationship attributes should be set.
        instance = serializer.save()
        assert instance.foreign_key.pk == new_foreign_key.pk
        assert instance.one_to_one.pk == new_one_to_one.pk
        assert [
            item.pk for item in instance.many_to_many.all()
        ] == [
            item.pk for item in new_many_to_many
        ]
        assert list(instance.through.all()) == []

        # Representation should be correct.
        expected = {
            'id': instance.pk,
            'foreign_key': new_foreign_key.pk,
            'one_to_one': new_one_to_one.pk,
            'many_to_many': [item.pk for item in new_many_to_many],
            'through': []
        }
        self.assertEqual(serializer.data, expected)

    def test_pk_update(self):
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = RelationalModel
                fields = '__all__'

        new_foreign_key = ForeignKeyTargetModel.objects.create(
            name='foreign_key'
        )
        new_one_to_one = OneToOneTargetModel.objects.create(
            name='one_to_one'
        )
        new_many_to_many = [
            ManyToManyTargetModel.objects.create(
                name='new many_to_many (%d)' % idx
            ) for idx in range(3)
        ]
        data = {
            'foreign_key': new_foreign_key.pk,
            'one_to_one': new_one_to_one.pk,
            'many_to_many': [item.pk for item in new_many_to_many],
        }

        # Serializer should validate okay.
        serializer = TestSerializer(self.instance, data=data)
        assert serializer.is_valid()

        # Creating the instance, relationship attributes should be set.
        instance = serializer.save()
        assert instance.foreign_key.pk == new_foreign_key.pk
        assert instance.one_to_one.pk == new_one_to_one.pk
        assert [
            item.pk for item in instance.many_to_many.all()
        ] == [
            item.pk for item in new_many_to_many
        ]
        assert list(instance.through.all()) == []

        # Representation should be correct.
        expected = {
            'id': self.instance.pk,
            'foreign_key': new_foreign_key.pk,
            'one_to_one': new_one_to_one.pk,
            'many_to_many': [item.pk for item in new_many_to_many],
            'through': []
        }
        self.assertEqual(serializer.data, expected)


# Tests for bulk create using `ListSerializer`.

class BulkCreateModel(models.Model):
    name = models.CharField(max_length=10)


class TestBulkCreate(TestCase):
    def test_bulk_create(self):
        class BasicModelSerializer(serializers.ModelSerializer):
            class Meta:
                model = BulkCreateModel
                fields = ('name',)

        class BulkCreateSerializer(serializers.ListSerializer):
            child = BasicModelSerializer()

        data = [{'name': 'a'}, {'name': 'b'}, {'name': 'c'}]
        serializer = BulkCreateSerializer(data=data)
        assert serializer.is_valid()

        # Objects are returned by save().
        instances = serializer.save()
        assert len(instances) == 3
        assert [item.name for item in instances] == ['a', 'b', 'c']

        # Objects have been created in the database.
        assert BulkCreateModel.objects.count() == 3
        assert list(BulkCreateModel.objects.values_list('name', flat=True)) == ['a', 'b', 'c']

        # Serializer returns correct data.
        assert serializer.data == data


class MetaClassTestModel(models.Model):
    text = models.CharField(max_length=100)


class TestSerializerMetaClass(TestCase):
    def test_meta_class_fields_option(self):
        class ExampleSerializer(serializers.ModelSerializer):
            class Meta:
                model = MetaClassTestModel
                fields = 'text'

        msginitial = "The `fields` option must be a list or tuple"
        with self.assertRaisesMessage(TypeError, msginitial):
            ExampleSerializer().fields

    def test_meta_class_exclude_option(self):
        class ExampleSerializer(serializers.ModelSerializer):
            class Meta:
                model = MetaClassTestModel
                exclude = 'text'

        msginitial = "The `exclude` option must be a list or tuple"
        with self.assertRaisesMessage(TypeError, msginitial):
            ExampleSerializer().fields

    def test_meta_class_fields_and_exclude_options(self):
        class ExampleSerializer(serializers.ModelSerializer):
            class Meta:
                model = MetaClassTestModel
                fields = ('text',)
                exclude = ('text',)

        msginitial = "Cannot set both 'fields' and 'exclude' options on serializer ExampleSerializer."
        with self.assertRaisesMessage(AssertionError, msginitial):
            ExampleSerializer().fields

    def test_declared_fields_with_exclude_option(self):
        class ExampleSerializer(serializers.ModelSerializer):
            text = serializers.CharField()

            class Meta:
                model = MetaClassTestModel
                exclude = ('text',)

        expected = (
            "Cannot both declare the field 'text' and include it in the "
            "ExampleSerializer 'exclude' option. Remove the field or, if "
            "inherited from a parent serializer, disable with `text = None`."
        )
        with self.assertRaisesMessage(AssertionError, expected):
            ExampleSerializer().fields


class Issue2704TestCase(TestCase):
    def test_queryset_all(self):
        class TestSerializer(serializers.ModelSerializer):
            additional_attr = serializers.CharField()

            class Meta:
                model = OneFieldModel
                fields = ('char_field', 'additional_attr')

        OneFieldModel.objects.create(char_field='abc')
        qs = OneFieldModel.objects.all()

        for o in qs:
            o.additional_attr = '123'

        serializer = TestSerializer(instance=qs, many=True)

        expected = [{
            'char_field': 'abc',
            'additional_attr': '123',
        }]

        assert serializer.data == expected


class Issue7550FooModel(models.Model):
    text = models.CharField(max_length=100)
    bar = models.ForeignKey(
        'Issue7550BarModel', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='foos', related_query_name='foo')


class Issue7550BarModel(models.Model):
    pass


class Issue7550TestCase(TestCase):

    def test_dotted_source(self):

        class _FooSerializer(serializers.ModelSerializer):
            class Meta:
                model = Issue7550FooModel
                fields = ('id', 'text')

        class FooSerializer(serializers.ModelSerializer):
            other_foos = _FooSerializer(source='bar.foos', many=True)

            class Meta:
                model = Issue7550BarModel
                fields = ('id', 'other_foos')

        bar = Issue7550BarModel.objects.create()
        foo_a = Issue7550FooModel.objects.create(bar=bar, text='abc')
        foo_b = Issue7550FooModel.objects.create(bar=bar, text='123')

        assert FooSerializer(foo_a).data == {
            'id': foo_a.id,
            'other_foos': [
                {
                    'id': foo_a.id,
                    'text': foo_a.text,
                },
                {
                    'id': foo_b.id,
                    'text': foo_b.text,
                },
            ],
        }

    def test_dotted_source_with_default(self):

        class _FooSerializer(serializers.ModelSerializer):
            class Meta:
                model = Issue7550FooModel
                fields = ('id', 'text')

        class FooSerializer(serializers.ModelSerializer):
            other_foos = _FooSerializer(source='bar.foos', default=[], many=True)

            class Meta:
                model = Issue7550FooModel
                fields = ('id', 'other_foos')

        foo = Issue7550FooModel.objects.create(bar=None, text='abc')

        assert FooSerializer(foo).data == {
            'id': foo.id,
            'other_foos': [],
        }


class DecimalFieldModel(models.Model):
    decimal_field = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        validators=[MinValueValidator(1), MaxValueValidator(3)]
    )


class TestDecimalFieldMappings(TestCase):
    def test_decimal_field_has_decimal_validator(self):
        """
        Test that a `DecimalField` has no `DecimalValidator`.
        """
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = DecimalFieldModel
                fields = '__all__'

        serializer = TestSerializer()

        assert len(serializer.fields['decimal_field'].validators) == 2

    def test_min_value_is_passed(self):
        """
        Test that the `MinValueValidator` is converted to the `min_value`
        argument for the field.
        """
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = DecimalFieldModel
                fields = '__all__'

        serializer = TestSerializer()

        assert serializer.fields['decimal_field'].min_value == 1

    def test_max_value_is_passed(self):
        """
        Test that the `MaxValueValidator` is converted to the `max_value`
        argument for the field.
        """
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = DecimalFieldModel
                fields = '__all__'

        serializer = TestSerializer()

        assert serializer.fields['decimal_field'].max_value == 3


class TestMetaInheritance(TestCase):
    def test_extra_kwargs_not_altered(self):
        class TestSerializer(serializers.ModelSerializer):
            non_model_field = serializers.CharField()

            class Meta:
                model = OneFieldModel
                read_only_fields = ('char_field', 'non_model_field')
                fields = read_only_fields
                extra_kwargs = {}

        class ChildSerializer(TestSerializer):
            class Meta(TestSerializer.Meta):
                read_only_fields = ()

        test_expected = dedent("""
            TestSerializer():
                char_field = CharField(read_only=True)
                non_model_field = CharField()
        """)

        child_expected = dedent("""
            ChildSerializer():
                char_field = CharField(max_length=100)
                non_model_field = CharField()
        """)
        self.assertEqual(repr(ChildSerializer()), child_expected)
        self.assertEqual(repr(TestSerializer()), test_expected)
        self.assertEqual(repr(ChildSerializer()), child_expected)


class OneToOneTargetTestModel(models.Model):
    text = models.CharField(max_length=100)


class OneToOneSourceTestModel(models.Model):
    target = models.OneToOneField(OneToOneTargetTestModel, primary_key=True, on_delete=models.CASCADE)


class TestModelFieldValues(TestCase):
    def test_model_field(self):
        class ExampleSerializer(serializers.ModelSerializer):
            class Meta:
                model = OneToOneSourceTestModel
                fields = ('target',)

        target = OneToOneTargetTestModel(id=1, text='abc')
        source = OneToOneSourceTestModel(target=target)
        serializer = ExampleSerializer(source)
        self.assertEqual(serializer.data, {'target': 1})


class TestUniquenessOverride(TestCase):
    def test_required_not_overwritten(self):
        class TestModel(models.Model):
            field_1 = models.IntegerField(null=True)
            field_2 = models.IntegerField()

            class Meta:
                unique_together = (('field_1', 'field_2'),)

        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = TestModel
                fields = '__all__'
                extra_kwargs = {'field_1': {'required': False}}

        fields = TestSerializer().fields
        self.assertFalse(fields['field_1'].required)
        self.assertTrue(fields['field_2'].required)


class Issue3674Test(TestCase):
    def test_nonPK_foreignkey_model_serializer(self):
        class TestParentModel(models.Model):
            title = models.CharField(max_length=64)

        class TestChildModel(models.Model):
            parent = models.ForeignKey(TestParentModel, related_name='children', on_delete=models.CASCADE)
            value = models.CharField(primary_key=True, max_length=64)

        class TestChildModelSerializer(serializers.ModelSerializer):
            class Meta:
                model = TestChildModel
                fields = ('value', 'parent')

        class TestParentModelSerializer(serializers.ModelSerializer):
            class Meta:
                model = TestParentModel
                fields = ('id', 'title', 'children')

        parent_expected = dedent("""
            TestParentModelSerializer():
                id = IntegerField(label='ID', read_only=True)
                title = CharField(max_length=64)
                children = PrimaryKeyRelatedField(many=True, queryset=TestChildModel.objects.all())
        """)
        self.assertEqual(repr(TestParentModelSerializer()), parent_expected)

        child_expected = dedent("""
            TestChildModelSerializer():
                value = CharField(max_length=64, validators=[<UniqueValidator(queryset=TestChildModel.objects.all())>])
                parent = PrimaryKeyRelatedField(queryset=TestParentModel.objects.all())
        """)
        self.assertEqual(repr(TestChildModelSerializer()), child_expected)

    def test_nonID_PK_foreignkey_model_serializer(self):

        class TestChildModelSerializer(serializers.ModelSerializer):
            class Meta:
                model = Issue3674ChildModel
                fields = ('value', 'parent')

        class TestParentModelSerializer(serializers.ModelSerializer):
            class Meta:
                model = Issue3674ParentModel
                fields = ('id', 'title', 'children')

        parent = Issue3674ParentModel.objects.create(title='abc')
        child = Issue3674ChildModel.objects.create(value='def', parent=parent)

        parent_serializer = TestParentModelSerializer(parent)
        child_serializer = TestChildModelSerializer(child)

        parent_expected = {'children': ['def'], 'id': 1, 'title': 'abc'}
        self.assertEqual(parent_serializer.data, parent_expected)

        child_expected = {'parent': 1, 'value': 'def'}
        self.assertEqual(child_serializer.data, child_expected)


class Issue4897TestCase(TestCase):
    def test_should_assert_if_writing_readonly_fields(self):
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = OneFieldModel
                fields = ('char_field',)
                readonly_fields = fields

        obj = OneFieldModel.objects.create(char_field='abc')

        with pytest.raises(AssertionError) as cm:
            TestSerializer(obj).fields
        cm.match(r'readonly_fields')


class Test5004UniqueChoiceField(TestCase):
    def test_unique_choice_field(self):
        class TestUniqueChoiceSerializer(serializers.ModelSerializer):
            class Meta:
                model = UniqueChoiceModel
                fields = '__all__'

        UniqueChoiceModel.objects.create(name='choice1')
        serializer = TestUniqueChoiceSerializer(data={'name': 'choice1'})
        assert not serializer.is_valid()
        assert serializer.errors == {'name': ['unique choice model with this name already exists.']}


class TestFieldSource(TestCase):
    def test_traverse_nullable_fk(self):
        """
        A dotted source with nullable elements uses default when any item in the chain is None. #5849.

        Similar to model example from test_serializer.py `test_default_for_multiple_dotted_source` method,
        but using RelatedField, rather than CharField.
        """
        class TestSerializer(serializers.ModelSerializer):
            target = serializers.PrimaryKeyRelatedField(
                source='target.target', read_only=True, allow_null=True, default=None
            )

            class Meta:
                model = NestedForeignKeySource
                fields = ('target', )

        model = NestedForeignKeySource.objects.create()
        assert TestSerializer(model).data['target'] is None

    def test_named_field_source(self):
        class TestSerializer(serializers.ModelSerializer):

            class Meta:
                model = RegularFieldsModel
                fields = ('number_field',)
                extra_kwargs = {
                    'number_field': {
                        'source': 'integer_field'
                    }
                }

        expected = dedent(r"""
            TestSerializer\(\):
                number_field = IntegerField\(.*source='integer_field'\)
        """)
        self.maxDiff = None
        assert re.search(expected, repr(TestSerializer())) is not None


class Issue6110TestModel(models.Model):
    """Model without .objects manager."""

    name = models.CharField(max_length=64)
    all_objects = models.Manager()


class Issue6110ModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Issue6110TestModel
        fields = ('name',)


class Issue6110Test(TestCase):
    def test_model_serializer_custom_manager(self):
        instance = Issue6110ModelSerializer().create({'name': 'test_name'})
        self.assertEqual(instance.name, 'test_name')

    def test_model_serializer_custom_manager_error_message(self):
        msginitial = ('Got a `TypeError` when calling `Issue6110TestModel.all_objects.create()`.')
        with self.assertRaisesMessage(TypeError, msginitial):
            Issue6110ModelSerializer().create({'wrong_param': 'wrong_param'})


class Issue6751Model(models.Model):
    many_to_many = models.ManyToManyField(ManyToManyTargetModel, related_name='+')
    char_field = models.CharField(max_length=100)
    char_field2 = models.CharField(max_length=100)


@receiver(m2m_changed, sender=Issue6751Model.many_to_many.through)
def process_issue6751model_m2m_changed(action, instance, **_):
    if action == 'post_add':
        instance.char_field = 'value changed by signal'
        instance.save()


class Issue6751Test(TestCase):
    def test_model_serializer_save_m2m_after_instance(self):
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = Issue6751Model
                fields = (
                    'many_to_many',
                    'char_field',
                )

        instance = Issue6751Model.objects.create(char_field='initial value')
        m2m_target = ManyToManyTargetModel.objects.create(name='target')

        serializer = TestSerializer(
            instance=instance,
            data={
                'many_to_many': (m2m_target.id,),
                'char_field': 'will be changed by signal',
            }
        )

        serializer.is_valid()
        serializer.save()

        self.assertEqual(instance.char_field, 'value changed by signal')
