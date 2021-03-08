import inspect
import pickle
import re
import sys
from collections import ChainMap
from collections.abc import Mapping

import pytest
from django.db import models

from rest_framework import exceptions, fields, relations, serializers
from rest_framework.fields import Field

from .models import (
    ForeignKeyTarget, NestedForeignKeySource, NullableForeignKeySource
)
from .utils import MockObject


# Test serializer fields imports.
# -------------------------------
class TestFieldImports:
    def is_field(self, name, value):
        return (
            isinstance(value, type) and
            issubclass(value, Field) and
            not name.startswith('_')
        )

    def test_fields(self):
        msg = "Expected `fields.%s` to be imported in `serializers`"
        field_classes = [
            key for key, value
            in inspect.getmembers(fields)
            if self.is_field(key, value)
        ]

        # sanity check
        assert 'Field' in field_classes
        assert 'BooleanField' in field_classes

        for field in field_classes:
            assert hasattr(serializers, field), msg % field

    def test_relations(self):
        msg = "Expected `relations.%s` to be imported in `serializers`"
        field_classes = [
            key for key, value
            in inspect.getmembers(relations)
            if self.is_field(key, value)
        ]

        # sanity check
        assert 'RelatedField' in field_classes

        for field in field_classes:
            assert hasattr(serializers, field), msg % field


# Tests for core functionality.
# -----------------------------

class TestSerializer:
    def setup(self):
        class ExampleSerializer(serializers.Serializer):
            char = serializers.CharField()
            integer = serializers.IntegerField()
        self.Serializer = ExampleSerializer

    def test_valid_serializer(self):
        serializer = self.Serializer(data={'char': 'abc', 'integer': 123})
        assert serializer.is_valid()
        assert serializer.validated_data == {'char': 'abc', 'integer': 123}
        assert serializer.data == {'char': 'abc', 'integer': 123}
        assert serializer.errors == {}

    def test_invalid_serializer(self):
        serializer = self.Serializer(data={'char': 'abc'})
        assert not serializer.is_valid()
        assert serializer.validated_data == {}
        assert serializer.data == {'char': 'abc'}
        assert serializer.errors == {'integer': ['This field is required.']}

    def test_invalid_datatype(self):
        serializer = self.Serializer(data=[{'char': 'abc'}])
        assert not serializer.is_valid()
        assert serializer.validated_data == {}
        assert serializer.data == {}
        assert serializer.errors == {'non_field_errors': ['Invalid data. Expected a dictionary, but got list.']}

    def test_partial_validation(self):
        serializer = self.Serializer(data={'char': 'abc'}, partial=True)
        assert serializer.is_valid()
        assert serializer.validated_data == {'char': 'abc'}
        assert serializer.errors == {}

    def test_empty_serializer(self):
        serializer = self.Serializer()
        assert serializer.data == {'char': '', 'integer': None}

    def test_missing_attribute_during_serialization(self):
        class MissingAttributes:
            pass
        instance = MissingAttributes()
        serializer = self.Serializer(instance)
        with pytest.raises(AttributeError):
            serializer.data

    def test_data_access_before_save_raises_error(self):
        def create(validated_data):
            return validated_data
        serializer = self.Serializer(data={'char': 'abc', 'integer': 123})
        serializer.create = create
        assert serializer.is_valid()
        assert serializer.data == {'char': 'abc', 'integer': 123}
        with pytest.raises(AssertionError):
            serializer.save()

    def test_validate_none_data(self):
        data = None
        serializer = self.Serializer(data=data)
        assert not serializer.is_valid()
        assert serializer.errors == {'non_field_errors': ['No data provided']}

    def test_serialize_chainmap(self):
        data = ChainMap({'char': 'abc'}, {'integer': 123})
        serializer = self.Serializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data == {'char': 'abc', 'integer': 123}
        assert serializer.errors == {}

    def test_serialize_custom_mapping(self):
        class SinglePurposeMapping(Mapping):
            def __getitem__(self, key):
                return 'abc' if key == 'char' else 123

            def __iter__(self):
                yield 'char'
                yield 'integer'

            def __len__(self):
                return 2

        serializer = self.Serializer(data=SinglePurposeMapping())
        assert serializer.is_valid()
        assert serializer.validated_data == {'char': 'abc', 'integer': 123}
        assert serializer.errors == {}

    def test_custom_to_internal_value(self):
        """
        to_internal_value() is expected to return a dict, but subclasses may
        return application specific type.
        """
        class Point:
            def __init__(self, srid, x, y):
                self.srid = srid
                self.coords = (x, y)

        # Declares a serializer that converts data into an object
        class NestedPointSerializer(serializers.Serializer):
            longitude = serializers.FloatField(source='x')
            latitude = serializers.FloatField(source='y')

            def to_internal_value(self, data):
                kwargs = super().to_internal_value(data)
                return Point(srid=4326, **kwargs)

        serializer = NestedPointSerializer(data={'longitude': 6.958307, 'latitude': 50.941357})
        assert serializer.is_valid()
        assert isinstance(serializer.validated_data, Point)
        assert serializer.validated_data.srid == 4326
        assert serializer.validated_data.coords[0] == 6.958307
        assert serializer.validated_data.coords[1] == 50.941357
        assert serializer.errors == {}

    def test_iterable_validators(self):
        """
        Ensure `validators` parameter is compatible with reasonable iterables.
        """
        data = {'char': 'abc', 'integer': 123}

        for validators in ([], (), set()):
            class ExampleSerializer(serializers.Serializer):
                char = serializers.CharField(validators=validators)
                integer = serializers.IntegerField()

            serializer = ExampleSerializer(data=data)
            assert serializer.is_valid()
            assert serializer.validated_data == data
            assert serializer.errors == {}

        def raise_exception(value):
            raise exceptions.ValidationError('Raised error')

        for validators in ([raise_exception], (raise_exception,), {raise_exception}):
            class ExampleSerializer(serializers.Serializer):
                char = serializers.CharField(validators=validators)
                integer = serializers.IntegerField()

            serializer = ExampleSerializer(data=data)
            assert not serializer.is_valid()
            assert serializer.data == data
            assert serializer.validated_data == {}
            assert serializer.errors == {'char': [
                exceptions.ErrorDetail(string='Raised error', code='invalid')
            ]}

    @pytest.mark.skipif(
        sys.version_info < (3, 7),
        reason="subscriptable classes requires Python 3.7 or higher",
    )
    def test_serializer_is_subscriptable(self):
        assert serializers.Serializer is serializers.Serializer["foo"]


class TestValidateMethod:
    def test_non_field_error_validate_method(self):
        class ExampleSerializer(serializers.Serializer):
            char = serializers.CharField()
            integer = serializers.IntegerField()

            def validate(self, attrs):
                raise serializers.ValidationError('Non field error')

        serializer = ExampleSerializer(data={'char': 'abc', 'integer': 123})
        assert not serializer.is_valid()
        assert serializer.errors == {'non_field_errors': ['Non field error']}

    def test_field_error_validate_method(self):
        class ExampleSerializer(serializers.Serializer):
            char = serializers.CharField()
            integer = serializers.IntegerField()

            def validate(self, attrs):
                raise serializers.ValidationError({'char': 'Field error'})

        serializer = ExampleSerializer(data={'char': 'abc', 'integer': 123})
        assert not serializer.is_valid()
        assert serializer.errors == {'char': ['Field error']}


class TestBaseSerializer:
    def setup(self):
        class ExampleSerializer(serializers.BaseSerializer):
            def to_representation(self, obj):
                return {
                    'id': obj['id'],
                    'email': obj['name'] + '@' + obj['domain']
                }

            def to_internal_value(self, data):
                name, domain = str(data['email']).split('@')
                return {
                    'id': int(data['id']),
                    'name': name,
                    'domain': domain,
                }

        self.Serializer = ExampleSerializer

    def test_abstract_methods_raise_proper_errors(self):
        serializer = serializers.BaseSerializer()
        with pytest.raises(NotImplementedError):
            serializer.to_internal_value(None)
        with pytest.raises(NotImplementedError):
            serializer.to_representation(None)
        with pytest.raises(NotImplementedError):
            serializer.update(None, None)
        with pytest.raises(NotImplementedError):
            serializer.create(None)

    def test_access_to_data_attribute_before_validation_raises_error(self):
        serializer = serializers.BaseSerializer(data={'foo': 'bar'})
        with pytest.raises(AssertionError):
            serializer.data

    def test_access_to_errors_attribute_before_validation_raises_error(self):
        serializer = serializers.BaseSerializer(data={'foo': 'bar'})
        with pytest.raises(AssertionError):
            serializer.errors

    def test_access_to_validated_data_attribute_before_validation_raises_error(self):
        serializer = serializers.BaseSerializer(data={'foo': 'bar'})
        with pytest.raises(AssertionError):
            serializer.validated_data

    def test_serialize_instance(self):
        instance = {'id': 1, 'name': 'tom', 'domain': 'example.com'}
        serializer = self.Serializer(instance)
        assert serializer.data == {'id': 1, 'email': 'tom@example.com'}

    def test_serialize_list(self):
        instances = [
            {'id': 1, 'name': 'tom', 'domain': 'example.com'},
            {'id': 2, 'name': 'ann', 'domain': 'example.com'},
        ]
        serializer = self.Serializer(instances, many=True)
        assert serializer.data == [
            {'id': 1, 'email': 'tom@example.com'},
            {'id': 2, 'email': 'ann@example.com'}
        ]

    def test_validate_data(self):
        data = {'id': 1, 'email': 'tom@example.com'}
        serializer = self.Serializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data == {
            'id': 1,
            'name': 'tom',
            'domain': 'example.com'
        }

    def test_validate_list(self):
        data = [
            {'id': 1, 'email': 'tom@example.com'},
            {'id': 2, 'email': 'ann@example.com'},
        ]
        serializer = self.Serializer(data=data, many=True)
        assert serializer.is_valid()
        assert serializer.validated_data == [
            {'id': 1, 'name': 'tom', 'domain': 'example.com'},
            {'id': 2, 'name': 'ann', 'domain': 'example.com'}
        ]


class TestStarredSource:
    """
    Tests for `source='*'` argument, which is often used for complex field or
    nested representations.

    For example:

        nested_field = NestedField(source='*')
    """
    data = {
        'nested1': {'a': 1, 'b': 2},
        'nested2': {'c': 3, 'd': 4}
    }

    def setup(self):
        class NestedSerializer1(serializers.Serializer):
            a = serializers.IntegerField()
            b = serializers.IntegerField()

        class NestedSerializer2(serializers.Serializer):
            c = serializers.IntegerField()
            d = serializers.IntegerField()

        class NestedBaseSerializer(serializers.Serializer):
            nested1 = NestedSerializer1(source='*')
            nested2 = NestedSerializer2(source='*')

        # nullable nested serializer testing
        class NullableNestedSerializer(serializers.Serializer):
            nested = NestedSerializer1(source='*', allow_null=True)

        # nullable custom field testing
        class CustomField(serializers.Field):
            def to_representation(self, instance):
                return getattr(instance, 'foo', None)

            def to_internal_value(self, data):
                return {'foo': data}

        class NullableFieldSerializer(serializers.Serializer):
            field = CustomField(source='*', allow_null=True)

        self.Serializer = NestedBaseSerializer
        self.NullableNestedSerializer = NullableNestedSerializer
        self.NullableFieldSerializer = NullableFieldSerializer

    def test_nested_validate(self):
        """
        A nested representation is validated into a flat internal object.
        """
        serializer = self.Serializer(data=self.data)
        assert serializer.is_valid()
        assert serializer.validated_data == {
            'a': 1,
            'b': 2,
            'c': 3,
            'd': 4
        }

    def test_nested_null_validate(self):
        serializer = self.NullableNestedSerializer(data={'nested': None})

        # validation should fail (but not error) since nested fields are required
        assert not serializer.is_valid()

    def test_nested_serialize(self):
        """
        An object can be serialized into a nested representation.
        """
        instance = {'a': 1, 'b': 2, 'c': 3, 'd': 4}
        serializer = self.Serializer(instance)
        assert serializer.data == self.data

    def test_field_validate(self):
        serializer = self.NullableFieldSerializer(data={'field': 'bar'})

        # validation should pass since no internal validation
        assert serializer.is_valid()
        assert serializer.validated_data == {'foo': 'bar'}

    def test_field_null_validate(self):
        serializer = self.NullableFieldSerializer(data={'field': None})

        # validation should pass since no internal validation
        assert serializer.is_valid()
        assert serializer.validated_data == {'foo': None}


class TestIncorrectlyConfigured:
    def test_incorrect_field_name(self):
        class ExampleSerializer(serializers.Serializer):
            incorrect_name = serializers.IntegerField()

        class ExampleObject:
            def __init__(self):
                self.correct_name = 123

        instance = ExampleObject()
        serializer = ExampleSerializer(instance)
        with pytest.raises(AttributeError) as exc_info:
            serializer.data
        msg = str(exc_info.value)
        assert msg.startswith(
            "Got AttributeError when attempting to get a value for field `incorrect_name` on serializer `ExampleSerializer`.\n"
            "The serializer field might be named incorrectly and not match any attribute or key on the `ExampleObject` instance.\n"
            "Original exception text was:"
        )


class TestNotRequiredOutput:
    def test_not_required_output_for_dict(self):
        """
        'required=False' should allow a dictionary key to be missing in output.
        """
        class ExampleSerializer(serializers.Serializer):
            omitted = serializers.CharField(required=False)
            included = serializers.CharField()

        serializer = ExampleSerializer(data={'included': 'abc'})
        serializer.is_valid()
        assert serializer.data == {'included': 'abc'}

    def test_not_required_output_for_object(self):
        """
        'required=False' should allow an object attribute to be missing in output.
        """
        class ExampleSerializer(serializers.Serializer):
            omitted = serializers.CharField(required=False)
            included = serializers.CharField()

            def create(self, validated_data):
                return MockObject(**validated_data)

        serializer = ExampleSerializer(data={'included': 'abc'})
        serializer.is_valid()
        serializer.save()
        assert serializer.data == {'included': 'abc'}


class TestDefaultOutput:
    def setup(self):
        class ExampleSerializer(serializers.Serializer):
            has_default = serializers.CharField(default='x')
            has_default_callable = serializers.CharField(default=lambda: 'y')
            no_default = serializers.CharField()
        self.Serializer = ExampleSerializer

    def test_default_used_for_dict(self):
        """
        'default="something"' should be used if dictionary key is missing from input.
        """
        serializer = self.Serializer({'no_default': 'abc'})
        assert serializer.data == {'has_default': 'x', 'has_default_callable': 'y', 'no_default': 'abc'}

    def test_default_used_for_object(self):
        """
        'default="something"' should be used if object attribute is missing from input.
        """
        instance = MockObject(no_default='abc')
        serializer = self.Serializer(instance)
        assert serializer.data == {'has_default': 'x', 'has_default_callable': 'y', 'no_default': 'abc'}

    def test_default_not_used_when_in_dict(self):
        """
        'default="something"' should not be used if dictionary key is present in input.
        """
        serializer = self.Serializer({'has_default': 'def', 'has_default_callable': 'ghi', 'no_default': 'abc'})
        assert serializer.data == {'has_default': 'def', 'has_default_callable': 'ghi', 'no_default': 'abc'}

    def test_default_not_used_when_in_object(self):
        """
        'default="something"' should not be used if object attribute is present in input.
        """
        instance = MockObject(has_default='def', has_default_callable='ghi', no_default='abc')
        serializer = self.Serializer(instance)
        assert serializer.data == {'has_default': 'def', 'has_default_callable': 'ghi', 'no_default': 'abc'}

    def test_default_for_dotted_source(self):
        """
        'default="something"' should be used when a traversed attribute is missing from input.
        """
        class Serializer(serializers.Serializer):
            traversed = serializers.CharField(default='x', source='traversed.attr')

        assert Serializer({}).data == {'traversed': 'x'}
        assert Serializer({'traversed': {}}).data == {'traversed': 'x'}
        assert Serializer({'traversed': None}).data == {'traversed': 'x'}

        assert Serializer({'traversed': {'attr': 'abc'}}).data == {'traversed': 'abc'}

    def test_default_for_multiple_dotted_source(self):
        class Serializer(serializers.Serializer):
            c = serializers.CharField(default='x', source='a.b.c')

        assert Serializer({}).data == {'c': 'x'}
        assert Serializer({'a': {}}).data == {'c': 'x'}
        assert Serializer({'a': None}).data == {'c': 'x'}
        assert Serializer({'a': {'b': {}}}).data == {'c': 'x'}
        assert Serializer({'a': {'b': None}}).data == {'c': 'x'}

        assert Serializer({'a': {'b': {'c': 'abc'}}}).data == {'c': 'abc'}

        # Same test using model objects to exercise both paths in
        # rest_framework.fields.get_attribute() (#5880)
        class ModelSerializer(serializers.Serializer):
            target = serializers.CharField(default='x', source='target.target.name')

        a = NestedForeignKeySource(name="Root Object", target=None)
        assert ModelSerializer(a).data == {'target': 'x'}

        b = NullableForeignKeySource(name="Intermediary Object", target=None)
        a.target = b
        assert ModelSerializer(a).data == {'target': 'x'}

        c = ForeignKeyTarget(name="Target Object")
        b.target = c
        assert ModelSerializer(a).data == {'target': 'Target Object'}

    def test_default_for_nested_serializer(self):
        class NestedSerializer(serializers.Serializer):
            a = serializers.CharField(default='1')
            c = serializers.CharField(default='2', source='b.c')

        class Serializer(serializers.Serializer):
            nested = NestedSerializer()

        assert Serializer({'nested': None}).data == {'nested': None}
        assert Serializer({'nested': {}}).data == {'nested': {'a': '1', 'c': '2'}}
        assert Serializer({'nested': {'a': '3', 'b': {}}}).data == {'nested': {'a': '3', 'c': '2'}}
        assert Serializer({'nested': {'a': '3', 'b': {'c': '4'}}}).data == {'nested': {'a': '3', 'c': '4'}}

    def test_default_for_allow_null(self):
        """
        Without an explicit default, allow_null implies default=None when serializing. #5518 #5708
        """
        class Serializer(serializers.Serializer):
            foo = serializers.CharField()
            bar = serializers.CharField(source='foo.bar', allow_null=True)
            optional = serializers.CharField(required=False, allow_null=True)

        # allow_null=True should imply default=None when serializing:
        assert Serializer({'foo': None}).data == {'foo': None, 'bar': None, 'optional': None, }


class TestCacheSerializerData:
    def test_cache_serializer_data(self):
        """
        Caching serializer data with pickle will drop the serializer info,
        but does preserve the data itself.
        """
        class ExampleSerializer(serializers.Serializer):
            field1 = serializers.CharField()
            field2 = serializers.CharField()

        serializer = ExampleSerializer({'field1': 'a', 'field2': 'b'})
        pickled = pickle.dumps(serializer.data)
        data = pickle.loads(pickled)
        assert data == {'field1': 'a', 'field2': 'b'}


class TestDefaultInclusions:
    def setup(self):
        class ExampleSerializer(serializers.Serializer):
            char = serializers.CharField(default='abc')
            integer = serializers.IntegerField()
        self.Serializer = ExampleSerializer

    def test_default_should_included_on_create(self):
        serializer = self.Serializer(data={'integer': 456})
        assert serializer.is_valid()
        assert serializer.validated_data == {'char': 'abc', 'integer': 456}
        assert serializer.errors == {}

    def test_default_should_be_included_on_update(self):
        instance = MockObject(char='def', integer=123)
        serializer = self.Serializer(instance, data={'integer': 456})
        assert serializer.is_valid()
        assert serializer.validated_data == {'char': 'abc', 'integer': 456}
        assert serializer.errors == {}

    def test_default_should_not_be_included_on_partial_update(self):
        instance = MockObject(char='def', integer=123)
        serializer = self.Serializer(instance, data={'integer': 456}, partial=True)
        assert serializer.is_valid()
        assert serializer.validated_data == {'integer': 456}
        assert serializer.errors == {}


class TestSerializerValidationWithCompiledRegexField:
    def setup(self):
        class ExampleSerializer(serializers.Serializer):
            name = serializers.RegexField(re.compile(r'\d'), required=True)
        self.Serializer = ExampleSerializer

    def test_validation_success(self):
        serializer = self.Serializer(data={'name': '2'})
        assert serializer.is_valid()
        assert serializer.validated_data == {'name': '2'}
        assert serializer.errors == {}


class Test2555Regression:
    def test_serializer_context(self):
        class NestedSerializer(serializers.Serializer):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                # .context should not cache
                self.context

        class ParentSerializer(serializers.Serializer):
            nested = NestedSerializer()

        serializer = ParentSerializer(data={}, context={'foo': 'bar'})
        assert serializer.context == {'foo': 'bar'}
        assert serializer.fields['nested'].context == {'foo': 'bar'}


class Test4606Regression:
    def setup(self):
        class ExampleSerializer(serializers.Serializer):
            name = serializers.CharField(required=True)
            choices = serializers.CharField(required=True)
        self.Serializer = ExampleSerializer

    def test_4606_regression(self):
        serializer = self.Serializer(data=[{"name": "liz"}], many=True)
        with pytest.raises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)


class TestDeclaredFieldInheritance:
    def test_declared_field_disabling(self):
        class Parent(serializers.Serializer):
            f1 = serializers.CharField()
            f2 = serializers.CharField()

        class Child(Parent):
            f1 = None

        class Grandchild(Child):
            pass

        assert len(Parent._declared_fields) == 2
        assert len(Child._declared_fields) == 1
        assert len(Grandchild._declared_fields) == 1

    def test_meta_field_disabling(self):
        # Declaratively setting a field on a child class will *not* prevent
        # the ModelSerializer from generating a default field.
        class MyModel(models.Model):
            f1 = models.CharField(max_length=10)
            f2 = models.CharField(max_length=10)

        class Parent(serializers.ModelSerializer):
            class Meta:
                model = MyModel
                fields = ['f1', 'f2']

        class Child(Parent):
            f1 = None

        class Grandchild(Child):
            pass

        assert len(Parent().get_fields()) == 2
        assert len(Child().get_fields()) == 2
        assert len(Grandchild().get_fields()) == 2

    def test_multiple_inheritance(self):
        class A(serializers.Serializer):
            field = serializers.CharField()

        class B(serializers.Serializer):
            field = serializers.IntegerField()

        class TestSerializer(A, B):
            pass

        fields = {
            name: type(f) for name, f
            in TestSerializer()._declared_fields.items()
        }
        assert fields == {
            'field': serializers.CharField,
        }

    def test_field_ordering(self):
        class Base(serializers.Serializer):
            f1 = serializers.CharField()
            f2 = serializers.CharField()

        class A(Base):
            f3 = serializers.IntegerField()

        class B(serializers.Serializer):
            f3 = serializers.CharField()
            f4 = serializers.CharField()

        class TestSerializer(A, B):
            f2 = serializers.IntegerField()
            f5 = serializers.CharField()

        fields = {
            name: type(f) for name, f
            in TestSerializer()._declared_fields.items()
        }

        # `IntegerField`s should be the 'winners' in field name conflicts
        # - `TestSerializer.f2` should override `Base.F2`
        # - `A.f3` should override `B.f3`
        assert fields == {
            'f1': serializers.CharField,
            'f2': serializers.IntegerField,
            'f3': serializers.IntegerField,
            'f4': serializers.CharField,
            'f5': serializers.CharField,
        }
