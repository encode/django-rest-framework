from decimal import Decimal

from pytest import mark

from datetime import datetime

from rest_framework import serializers
from .models import RegularFieldsModel, RegularFieldsAndFKModel


data = {
    'big_integer_field': 100000,
    'char_field': 'a',
    'comma_separated_integer_field': '1,2',
    'date_field': datetime.now().date(),
    'datetime_field': datetime.now(),
    'decimal_field': Decimal('1.5'),
    'email_field': 'somewhere@overtherainbow.com',
    'float_field': 0.443,
    'integer_field': 55,
    'null_boolean_field': True,
    'positive_integer_field': 1,
    'positive_small_integer_field': 1,
    'slug_field': 'slug-friendly-text',
    'small_integer_field': 1,
    'text_field': 'lorem ipsum',
    'time_field': datetime.now().time(),
    'url_field': 'https://overtherainbow.com'
}


class TestSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegularFieldsModel
        fields = data.keys() + ['method']


class TestNestedSerializer(serializers.ModelSerializer):
    fk = TestSerializer()

    class Meta:
        model = RegularFieldsAndFKModel
        fields = data.keys() + ['method', 'fk']


@mark.bench('serializers.ModelSerializer.get_fields')
def test_get_fields():
    instance = RegularFieldsModel(**data)
    serializer = TestSerializer(instance=instance)

    assert serializer.get_fields()


@mark.bench('serializers.ModelSerializer.to_representation')
def test_object_serialization():
    instance = RegularFieldsModel(**data)
    serializer = TestSerializer(instance=instance)

    assert serializer.data, serializer.errors


@mark.bench('serializers.ModelSerializer.to_representation')
def test_nested_object_serialization():
    nested_instance = RegularFieldsModel(**data)
    instance = RegularFieldsAndFKModel(fk=nested_instance, **data)
    serializer = TestSerializer(instance=instance)

    assert serializer.data, serializer.errors


@mark.bench('serializers.ModelSerializer.to_representation')
def test_object_list_serialization():
    instance = [RegularFieldsModel(**data) for _ in range(100)]
    serializer = TestSerializer(instance=instance, many=True)

    assert serializer.data, serializer.errors


@mark.bench('serializers.ModelSerializer.to_representation')
def test_object_serialization_with_partial_update():
    instance = RegularFieldsModel(**data)
    serializer = TestSerializer(instance=instance, data={'char_field': 'b'}, partial=True)

    assert serializer.is_valid(), serializer.errors
    assert serializer.data, serializer.errors


@mark.bench('serializers.ModelSerializer.to_representation')
def test_object_serialization_with_update():
    instance = RegularFieldsModel(**data)
    new_data = data.copy()
    new_data['char_field'] = 'b'
    serializer = TestSerializer(instance=instance, data=new_data)

    assert serializer.is_valid(), serializer.errors
    assert serializer.data, serializer.errors


@mark.bench('serializers.ModelSerializer.to_internal_value')
def test_object_deserialization():
    serializer = TestSerializer(data=data)

    assert serializer.is_valid(), serializer.errors


@mark.bench('serializers.ModelSerializer.to_internal_value')
def test_object_list_deserialization():
    serializer = TestSerializer(data=[data for _ in range(100)], many=True)

    assert serializer.is_valid(), serializer.errors


@mark.bench('serializers.ModelSerializer.__init__')
def test_serializer_initialization():
    TestSerializer(data=data)
