"""
The `ModelSerializer` and `HyperlinkedModelSerializer` classes are essentially
shortcuts for automatically creating serializers based on a given model class.

These tests deal with ensuring that we correctly map the model fields onto
an appropriate set of serializer fields for each case.
"""
from __future__ import unicode_literals

import decimal

import django
import pytest
from django.core.exceptions import ImproperlyConfigured
from django.core.validators import (
    MaxValueValidator, MinLengthValidator, MinValueValidator
)
from django.db import models
from django.test import TestCase
from django.utils import six

from rest_framework import serializers
from rest_framework.compat import DurationField as ModelDurationField
from rest_framework.compat import unicode_repr


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
    null_boolean_field = models.NullBooleanField()
    positive_integer_field = models.PositiveIntegerField()
    positive_small_integer_field = models.PositiveSmallIntegerField()
    slug_field = models.SlugField(max_length=100)
    small_integer_field = models.SmallIntegerField()
    text_field = models.TextField()
    time_field = models.TimeField()
    url_field = models.URLField(max_length=100)
    custom_field = CustomField()

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


class ChoicesModel(models.Model):
    choices_field_with_nonstandard_args = models.DecimalField(max_digits=3, decimal_places=1, choices=DECIMAL_CHOICES, verbose_name='A label')


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
        with self.assertRaises(TypeError) as excinfo:
            serializer.save()
        msginitial = 'Got a `TypeError` when calling `OneFieldModel.objects.create()`.'
        assert str(excinfo.exception).startswith(msginitial)

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
        with self.assertRaises(ValueError) as excinfo:
            serializer.is_valid()
        msginitial = 'Cannot use ModelSerializer with Abstract Models.'
        assert str(excinfo.exception).startswith(msginitial)


class TestRegularFieldMappings(TestCase):
    def test_regular_fields(self):
        """
        Model fields should map to their equivelent serializer fields.
        """
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = RegularFieldsModel

        expected = dedent("""
            TestSerializer():
                auto_field = IntegerField(read_only=True)
                big_integer_field = IntegerField()
                boolean_field = BooleanField(required=False)
                char_field = CharField(max_length=100)
                comma_separated_integer_field = CharField(max_length=100, validators=[<django.core.validators.RegexValidator object>])
                date_field = DateField()
                datetime_field = DateTimeField()
                decimal_field = DecimalField(decimal_places=1, max_digits=3)
                email_field = EmailField(max_length=100)
                float_field = FloatField()
                integer_field = IntegerField()
                null_boolean_field = NullBooleanField(required=False)
                positive_integer_field = IntegerField()
                positive_small_integer_field = IntegerField()
                slug_field = SlugField(max_length=100)
                small_integer_field = IntegerField()
                text_field = CharField(style={'base_template': 'textarea.html'})
                time_field = TimeField()
                url_field = URLField(max_length=100)
                custom_field = ModelField(model_field=<tests.test_model_serializer.CustomField: custom_field>)
        """)
        self.assertEqual(unicode_repr(TestSerializer()), expected)

    def test_field_options(self):
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = FieldOptionsModel

        expected = dedent("""
            TestSerializer():
                id = IntegerField(label='ID', read_only=True)
                value_limit_field = IntegerField(max_value=10, min_value=1)
                length_limit_field = CharField(max_length=12, min_length=3)
                blank_field = CharField(allow_blank=True, max_length=10, required=False)
                null_field = IntegerField(allow_null=True, required=False)
                default_field = IntegerField(required=False)
                descriptive_field = IntegerField(help_text='Some help text', label='A label')
                choices_field = ChoiceField(choices=(('red', 'Red'), ('blue', 'Blue'), ('green', 'Green')))
        """)
        if six.PY2:
            # This particular case is too awkward to resolve fully across
            # both py2 and py3.
            expected = expected.replace(
                "('red', 'Red'), ('blue', 'Blue'), ('green', 'Green')",
                "(u'red', u'Red'), (u'blue', u'Blue'), (u'green', u'Green')"
            )
        self.assertEqual(unicode_repr(TestSerializer()), expected)

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
        raise a configuration errror.
        """
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = RegularFieldsModel
                fields = ('auto_field', 'invalid')

        with self.assertRaises(ImproperlyConfigured) as excinfo:
            TestSerializer().fields
        expected = 'Field name `invalid` is not valid for model `RegularFieldsModel`.'
        assert str(excinfo.exception) == expected

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

        with self.assertRaises(AssertionError) as excinfo:
            TestSerializer().fields
        expected = (
            "The field 'missing' was declared on serializer TestSerializer, "
            "but has not been included in the 'fields' option."
        )
        assert str(excinfo.exception) == expected

    def test_missing_superclass_field(self):
        """
        Fields that have been declared on a parent of the serializer class may
        be excluded from the `Meta.fields` option.
        """
        class TestSerializer(serializers.ModelSerializer):
            missing = serializers.ReadOnlyField()

            class Meta:
                model = RegularFieldsModel

        class ChildSerializer(TestSerializer):
            missing = serializers.ReadOnlyField()

            class Meta:
                model = RegularFieldsModel
                fields = ('auto_field',)

        ChildSerializer().fields

    def test_choices_with_nonstandard_args(self):
        class ExampleSerializer(serializers.ModelSerializer):
            class Meta:
                model = ChoicesModel

        ExampleSerializer()


@pytest.mark.skipif(django.VERSION < (1, 8),
                    reason='DurationField is only available for django1.8+')
class TestDurationFieldMapping(TestCase):
    def test_duration_field(self):
        class DurationFieldModel(models.Model):
            """
            A model that defines DurationField.
            """
            duration_field = ModelDurationField()

        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = DurationFieldModel

        expected = dedent("""
            TestSerializer():
                id = IntegerField(label='ID', read_only=True)
                duration_field = DurationField()
        """)
        self.assertEqual(unicode_repr(TestSerializer()), expected)


class TestGenericIPAddressFieldValidation(TestCase):
    def test_ip_address_validation(self):
        class IPAddressFieldModel(models.Model):
            address = models.GenericIPAddressField()

        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = IPAddressFieldModel

        s = TestSerializer(data={'address': 'not an ip address'})
        self.assertFalse(s.is_valid())
        self.assertEquals(1, len(s.errors['address']),
                          'Unexpected number of validation errors: '
                          '{0}'.format(s.errors))


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
    forwards = models.ForeignKey('ThroughTargetModel')
    backwards = models.ForeignKey('RelationalModel')


class RelationalModel(models.Model):
    foreign_key = models.ForeignKey(ForeignKeyTargetModel, related_name='reverse_foreign_key')
    many_to_many = models.ManyToManyField(ManyToManyTargetModel, related_name='reverse_many_to_many')
    one_to_one = models.OneToOneField(OneToOneTargetModel, related_name='reverse_one_to_one')
    through = models.ManyToManyField(ThroughTargetModel, through=Supplementary, related_name='reverse_through')


class UniqueTogetherModel(models.Model):
    foreign_key = models.ForeignKey(ForeignKeyTargetModel, related_name='unique_foreign_key')
    one_to_one = models.OneToOneField(OneToOneTargetModel, related_name='unique_one_to_one')

    class Meta:
        unique_together = ("foreign_key", "one_to_one")


class TestRelationalFieldMappings(TestCase):
    def test_pk_relations(self):
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = RelationalModel

        expected = dedent("""
            TestSerializer():
                id = IntegerField(label='ID', read_only=True)
                foreign_key = PrimaryKeyRelatedField(queryset=ForeignKeyTargetModel.objects.all())
                one_to_one = PrimaryKeyRelatedField(queryset=OneToOneTargetModel.objects.all(), validators=[<UniqueValidator(queryset=RelationalModel.objects.all())>])
                many_to_many = PrimaryKeyRelatedField(allow_empty=False, many=True, queryset=ManyToManyTargetModel.objects.all())
                through = PrimaryKeyRelatedField(many=True, read_only=True)
        """)
        self.assertEqual(unicode_repr(TestSerializer()), expected)

    def test_nested_relations(self):
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = RelationalModel
                depth = 1

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
        self.assertEqual(unicode_repr(TestSerializer()), expected)

    def test_hyperlinked_relations(self):
        class TestSerializer(serializers.HyperlinkedModelSerializer):
            class Meta:
                model = RelationalModel

        expected = dedent("""
            TestSerializer():
                url = HyperlinkedIdentityField(view_name='relationalmodel-detail')
                foreign_key = HyperlinkedRelatedField(queryset=ForeignKeyTargetModel.objects.all(), view_name='foreignkeytargetmodel-detail')
                one_to_one = HyperlinkedRelatedField(queryset=OneToOneTargetModel.objects.all(), validators=[<UniqueValidator(queryset=RelationalModel.objects.all())>], view_name='onetoonetargetmodel-detail')
                many_to_many = HyperlinkedRelatedField(allow_empty=False, many=True, queryset=ManyToManyTargetModel.objects.all(), view_name='manytomanytargetmodel-detail')
                through = HyperlinkedRelatedField(many=True, read_only=True, view_name='throughtargetmodel-detail')
        """)
        self.assertEqual(unicode_repr(TestSerializer()), expected)

    def test_nested_hyperlinked_relations(self):
        class TestSerializer(serializers.HyperlinkedModelSerializer):
            class Meta:
                model = RelationalModel
                depth = 1

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
        self.assertEqual(unicode_repr(TestSerializer()), expected)

    def test_nested_unique_together_relations(self):
        class TestSerializer(serializers.HyperlinkedModelSerializer):
            class Meta:
                model = UniqueTogetherModel
                depth = 1
        expected = dedent("""
            TestSerializer():
                url = HyperlinkedIdentityField(view_name='uniquetogethermodel-detail')
                foreign_key = NestedSerializer(read_only=True):
                    url = HyperlinkedIdentityField(view_name='foreignkeytargetmodel-detail')
                    name = CharField(max_length=100)
                one_to_one = NestedSerializer(read_only=True):
                    url = HyperlinkedIdentityField(view_name='onetoonetargetmodel-detail')
                    name = CharField(max_length=100)
                class Meta:
                    validators = [<UniqueTogetherValidator(queryset=UniqueTogetherModel.objects.all(), fields=('foreign_key', 'one_to_one'))>]
        """)
        if six.PY2:
            # This case is also too awkward to resolve fully across both py2
            # and py3.  (See above)
            expected = expected.replace(
                "('foreign_key', 'one_to_one')",
                "(u'foreign_key', u'one_to_one')"
            )
        self.assertEqual(unicode_repr(TestSerializer()), expected)

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
        self.assertEqual(unicode_repr(TestSerializer()), expected)

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
        self.assertEqual(unicode_repr(TestSerializer()), expected)

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
        self.assertEqual(unicode_repr(TestSerializer()), expected)

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
        self.assertEqual(unicode_repr(TestSerializer()), expected)


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
        self.instance.many_to_many = self.many_to_many_targets
        self.instance.save()

    def test_pk_retrival(self):
        class TestSerializer(serializers.ModelSerializer):
            class Meta:
                model = RelationalModel

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


class TestMetaClassModel(models.Model):
    text = models.CharField(max_length=100)


class TestSerializerMetaClass(TestCase):
    def test_meta_class_fields_option(self):
        class ExampleSerializer(serializers.ModelSerializer):
            class Meta:
                model = TestMetaClassModel
                fields = 'text'

        with self.assertRaises(TypeError) as result:
            ExampleSerializer().fields

        exception = result.exception
        assert str(exception).startswith(
            "The `fields` option must be a list or tuple"
        )

    def test_meta_class_exclude_option(self):
        class ExampleSerializer(serializers.ModelSerializer):
            class Meta:
                model = TestMetaClassModel
                exclude = 'text'

        with self.assertRaises(TypeError) as result:
            ExampleSerializer().fields

        exception = result.exception
        assert str(exception).startswith(
            "The `exclude` option must be a list or tuple"
        )

    def test_meta_class_fields_and_exclude_options(self):
        class ExampleSerializer(serializers.ModelSerializer):
            class Meta:
                model = TestMetaClassModel
                fields = ('text',)
                exclude = ('text',)

        with self.assertRaises(AssertionError) as result:
            ExampleSerializer().fields

        exception = result.exception
        self.assertEqual(
            str(exception),
            "Cannot set both 'fields' and 'exclude' options on serializer ExampleSerializer."
        )


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
