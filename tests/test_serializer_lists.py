import sys

import pytest
from django.http import QueryDict
from django.utils.datastructures import MultiValueDict

from rest_framework import serializers
from rest_framework.exceptions import ErrorDetail
from tests.models import (
    CustomManagerModel, NullableOneToOneSource, OneToOneTarget
)


class BasicObject:
    """
    A mock object for testing serializer save behavior.
    """
    def __init__(self, **kwargs):
        self._data = kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __eq__(self, other):
        if self._data.keys() != other._data.keys():
            return False
        for key in self._data:
            if self._data[key] != other._data[key]:
                return False
        return True


class TestListSerializer:
    """
    Tests for using a ListSerializer as a top-level serializer.
    Note that this is in contrast to using ListSerializer as a field.
    """

    def setup_method(self):
        class IntegerListSerializer(serializers.ListSerializer):
            child = serializers.IntegerField()
        self.Serializer = IntegerListSerializer

    def test_validate(self):
        """
        Validating a list of items should return a list of validated items.
        """
        input_data = ["123", "456"]
        expected_output = [123, 456]
        serializer = self.Serializer(data=input_data)
        assert serializer.is_valid()
        assert serializer.validated_data == expected_output

    def test_validate_html_input(self):
        """
        HTML input should be able to mock list structures using [x] style ids.
        """
        input_data = MultiValueDict({"[0]": ["123"], "[1]": ["456"]})
        expected_output = [123, 456]
        serializer = self.Serializer(data=input_data)
        assert serializer.is_valid()
        assert serializer.validated_data == expected_output

    @pytest.mark.skipif(
        sys.version_info < (3, 7),
        reason="subscriptable classes requires Python 3.7 or higher",
    )
    def test_list_serializer_is_subscriptable(self):
        assert serializers.ListSerializer is serializers.ListSerializer["foo"]


class TestListSerializerContainingNestedSerializer:
    """
    Tests for using a ListSerializer containing another serializer.
    """

    def setup_method(self):
        class TestSerializer(serializers.Serializer):
            integer = serializers.IntegerField()
            boolean = serializers.BooleanField()

            def create(self, validated_data):
                return BasicObject(**validated_data)

        class ObjectListSerializer(serializers.ListSerializer):
            child = TestSerializer()

        self.Serializer = ObjectListSerializer

    def test_validate(self):
        """
        Validating a list of dictionaries should return a list of
        validated dictionaries.
        """
        input_data = [
            {"integer": "123", "boolean": "true"},
            {"integer": "456", "boolean": "false"}
        ]
        expected_output = [
            {"integer": 123, "boolean": True},
            {"integer": 456, "boolean": False}
        ]
        serializer = self.Serializer(data=input_data)
        assert serializer.is_valid()
        assert serializer.validated_data == expected_output

    def test_create(self):
        """
        Creating from a list of dictionaries should return a list of objects.
        """
        input_data = [
            {"integer": "123", "boolean": "true"},
            {"integer": "456", "boolean": "false"}
        ]
        expected_output = [
            BasicObject(integer=123, boolean=True),
            BasicObject(integer=456, boolean=False),
        ]
        serializer = self.Serializer(data=input_data)
        assert serializer.is_valid()
        assert serializer.save() == expected_output

    def test_serialize(self):
        """
        Serialization of a list of objects should return a list of dictionaries.
        """
        input_objects = [
            BasicObject(integer=123, boolean=True),
            BasicObject(integer=456, boolean=False)
        ]
        expected_output = [
            {"integer": 123, "boolean": True},
            {"integer": 456, "boolean": False}
        ]
        serializer = self.Serializer(input_objects)
        assert serializer.data == expected_output

    def test_validate_html_input(self):
        """
        HTML input should be able to mock list structures using [x]
        style prefixes.
        """
        input_data = MultiValueDict({
            "[0]integer": ["123"],
            "[0]boolean": ["true"],
            "[1]integer": ["456"],
            "[1]boolean": ["false"]
        })
        expected_output = [
            {"integer": 123, "boolean": True},
            {"integer": 456, "boolean": False}
        ]
        serializer = self.Serializer(data=input_data)
        assert serializer.is_valid()
        assert serializer.validated_data == expected_output

    def test_update_allow_custom_child_validation(self):
        """
        Update a list of objects thanks custom run_child_validation implementation.
        """

        class TestUpdateSerializer(serializers.Serializer):
            integer = serializers.IntegerField()
            boolean = serializers.BooleanField()

            def update(self, instance, validated_data):
                instance._data.update(validated_data)
                return instance

            def validate(self, data):
                # self.instance is set to current BasicObject instance
                assert isinstance(self.instance, BasicObject)
                # self.initial_data is current dictionary
                assert isinstance(self.initial_data, dict)
                assert self.initial_data["pk"] == self.instance.pk
                return super().validate(data)

        class ListUpdateSerializer(serializers.ListSerializer):
            child = TestUpdateSerializer()

            def run_child_validation(self, data):
                # find related instance in self.instance list
                child_instance = next(o for o in self.instance if o.pk == data["pk"])
                # set instance and initial_data for child serializer
                self.child.instance = child_instance
                self.child.initial_data = data
                return super().run_child_validation(data)

            def update(self, instance, validated_data):
                return [
                    self.child.update(instance, attrs)
                    for instance, attrs in zip(self.instance, validated_data)
                ]

        instance = [
            BasicObject(pk=1, integer=11, private_field="a"),
            BasicObject(pk=2, integer=22, private_field="b"),
        ]
        input_data = [
            {"pk": 1, "integer": "123", "boolean": "true"},
            {"pk": 2, "integer": "456", "boolean": "false"},
        ]
        expected_output = [
            BasicObject(pk=1, integer=123, boolean=True, private_field="a"),
            BasicObject(pk=2, integer=456, boolean=False, private_field="b"),
        ]
        serializer = ListUpdateSerializer(instance, data=input_data)
        assert serializer.is_valid()
        updated_instances = serializer.save()
        assert updated_instances == expected_output


class TestNestedListSerializer:
    """
    Tests for using a ListSerializer as a field.
    """

    def setup_method(self):
        class TestSerializer(serializers.Serializer):
            integers = serializers.ListSerializer(child=serializers.IntegerField())
            booleans = serializers.ListSerializer(child=serializers.BooleanField())

            def create(self, validated_data):
                return BasicObject(**validated_data)

        self.Serializer = TestSerializer

    def test_validate(self):
        """
        Validating a list of items should return a list of validated items.
        """
        input_data = {
            "integers": ["123", "456"],
            "booleans": ["true", "false"]
        }
        expected_output = {
            "integers": [123, 456],
            "booleans": [True, False]
        }
        serializer = self.Serializer(data=input_data)
        assert serializer.is_valid()
        assert serializer.validated_data == expected_output

    def test_create(self):
        """
        Creation with a list of items return an object with an attribute that
        is a list of items.
        """
        input_data = {
            "integers": ["123", "456"],
            "booleans": ["true", "false"]
        }
        expected_output = BasicObject(
            integers=[123, 456],
            booleans=[True, False]
        )
        serializer = self.Serializer(data=input_data)
        assert serializer.is_valid()
        assert serializer.save() == expected_output

    def test_serialize(self):
        """
        Serialization of a list of items should return a list of items.
        """
        input_object = BasicObject(
            integers=[123, 456],
            booleans=[True, False]
        )
        expected_output = {
            "integers": [123, 456],
            "booleans": [True, False]
        }
        serializer = self.Serializer(input_object)
        assert serializer.data == expected_output

    def test_validate_html_input(self):
        """
        HTML input should be able to mock list structures using [x]
        style prefixes.
        """
        input_data = MultiValueDict({
            "integers[0]": ["123"],
            "integers[1]": ["456"],
            "booleans[0]": ["true"],
            "booleans[1]": ["false"]
        })
        expected_output = {
            "integers": [123, 456],
            "booleans": [True, False]
        }
        serializer = self.Serializer(data=input_data)
        assert serializer.is_valid()
        assert serializer.validated_data == expected_output


class TestNestedListSerializerAllowEmpty:
    """Tests the behaviour of allow_empty=False when a ListSerializer is used as a field."""

    @pytest.mark.parametrize('partial', (False, True))
    def test_allow_empty_true(self, partial):
        """
        If allow_empty is True, empty lists should be allowed regardless of the value
        of partial on the parent serializer.
        """
        class ChildSerializer(serializers.Serializer):
            id = serializers.IntegerField()

        class ParentSerializer(serializers.Serializer):
            ids = ChildSerializer(many=True, allow_empty=True)

        serializer = ParentSerializer(data={'ids': []}, partial=partial)
        assert serializer.is_valid()
        assert serializer.validated_data == {
            'ids': [],
        }

    @pytest.mark.parametrize('partial', (False, True))
    def test_allow_empty_false(self, partial):
        """
        If allow_empty is False, empty lists should fail validation regardless of the value
        of partial on the parent serializer.
        """
        class ChildSerializer(serializers.Serializer):
            id = serializers.IntegerField()

        class ParentSerializer(serializers.Serializer):
            ids = ChildSerializer(many=True, allow_empty=False)

        serializer = ParentSerializer(data={'ids': []}, partial=partial)
        assert not serializer.is_valid()
        assert serializer.errors == {
            'ids': {
                'non_field_errors': [
                    ErrorDetail(string='This list may not be empty.', code='empty')],
            }
        }


class TestNestedListOfListsSerializer:
    def setup_method(self):
        class TestSerializer(serializers.Serializer):
            integers = serializers.ListSerializer(
                child=serializers.ListSerializer(
                    child=serializers.IntegerField()
                )
            )
            booleans = serializers.ListSerializer(
                child=serializers.ListSerializer(
                    child=serializers.BooleanField()
                )
            )

        self.Serializer = TestSerializer

    def test_validate(self):
        input_data = {
            'integers': [['123', '456'], ['789', '0']],
            'booleans': [['true', 'true'], ['false', 'true']]
        }
        expected_output = {
            "integers": [[123, 456], [789, 0]],
            "booleans": [[True, True], [False, True]]
        }
        serializer = self.Serializer(data=input_data)
        assert serializer.is_valid()
        assert serializer.validated_data == expected_output

    def test_validate_html_input(self):
        """
        HTML input should be able to mock lists of lists using [x][y]
        style prefixes.
        """
        input_data = MultiValueDict({
            "integers[0][0]": ["123"],
            "integers[0][1]": ["456"],
            "integers[1][0]": ["789"],
            "integers[1][1]": ["000"],
            "booleans[0][0]": ["true"],
            "booleans[0][1]": ["true"],
            "booleans[1][0]": ["false"],
            "booleans[1][1]": ["true"]
        })
        expected_output = {
            "integers": [[123, 456], [789, 0]],
            "booleans": [[True, True], [False, True]]
        }
        serializer = self.Serializer(data=input_data)
        assert serializer.is_valid()
        assert serializer.validated_data == expected_output


class TestListSerializerClass:
    """Tests for a custom list_serializer_class."""
    def test_list_serializer_class_validate(self):
        class CustomListSerializer(serializers.ListSerializer):
            def validate(self, attrs):
                raise serializers.ValidationError('Non field error')

        class TestSerializer(serializers.Serializer):
            class Meta:
                list_serializer_class = CustomListSerializer

        serializer = TestSerializer(data=[], many=True)
        assert not serializer.is_valid()
        assert serializer.errors == {'non_field_errors': ['Non field error']}


class TestSerializerPartialUsage:
    """
    When not submitting key for list fields or multiple choice, partial
    serialization should result in an empty state (key not there), not
    an empty list.

    Regression test for Github issue #2761.
    """
    def test_partial_listfield(self):
        class ListSerializer(serializers.Serializer):
            listdata = serializers.ListField()
        serializer = ListSerializer(data=MultiValueDict(), partial=True)
        result = serializer.to_internal_value(data={})
        assert "listdata" not in result
        assert serializer.is_valid()
        assert serializer.validated_data == {}
        assert serializer.errors == {}

    def test_partial_multiplechoice(self):
        class MultipleChoiceSerializer(serializers.Serializer):
            multiplechoice = serializers.MultipleChoiceField(choices=[1, 2, 3])
        serializer = MultipleChoiceSerializer(data=MultiValueDict(), partial=True)
        result = serializer.to_internal_value(data={})
        assert "multiplechoice" not in result
        assert serializer.is_valid()
        assert serializer.validated_data == {}
        assert serializer.errors == {}

    def test_allow_empty_true(self):
        class ListSerializer(serializers.Serializer):
            update_field = serializers.IntegerField()
            store_field = serializers.IntegerField()

        instance = [
            {'update_field': 11, 'store_field': 12},
            {'update_field': 21, 'store_field': 22},
        ]

        serializer = ListSerializer(instance, data=[], partial=True, many=True)
        assert serializer.is_valid()
        assert serializer.validated_data == []
        assert serializer.errors == []

    def test_update_allow_empty_true(self):
        class ListSerializer(serializers.Serializer):
            update_field = serializers.IntegerField()
            store_field = serializers.IntegerField()

        instance = [
            {'update_field': 11, 'store_field': 12},
            {'update_field': 21, 'store_field': 22},
        ]
        input_data = [{'update_field': 31}, {'update_field': 41}]
        updated_data_list = [
            {'update_field': 31, 'store_field': 12},
            {'update_field': 41, 'store_field': 22},
        ]

        serializer = ListSerializer(
            instance, data=input_data, partial=True, many=True)
        assert serializer.is_valid()

        for index, data in enumerate(serializer.validated_data):
            for key, value in data.items():
                assert value == updated_data_list[index][key]

        assert serializer.errors == []

    def test_allow_empty_false(self):
        class ListSerializer(serializers.Serializer):
            update_field = serializers.IntegerField()
            store_field = serializers.IntegerField()

        instance = [
            {'update_field': 11, 'store_field': 12},
            {'update_field': 21, 'store_field': 22},
        ]

        serializer = ListSerializer(
            instance, data=[], allow_empty=False, partial=True, many=True)
        assert not serializer.is_valid()
        assert serializer.validated_data == []
        assert len(serializer.errors) == 1
        assert serializer.errors['non_field_errors'][0] == 'This list may not be empty.'

    def test_update_allow_empty_false(self):
        class ListSerializer(serializers.Serializer):
            update_field = serializers.IntegerField()
            store_field = serializers.IntegerField()

        instance = [
            {'update_field': 11, 'store_field': 12},
            {'update_field': 21, 'store_field': 22},
        ]
        input_data = [{'update_field': 31}, {'update_field': 41}]
        updated_data_list = [
            {'update_field': 31, 'store_field': 12},
            {'update_field': 41, 'store_field': 22},
        ]

        serializer = ListSerializer(
            instance, data=input_data, allow_empty=False, partial=True, many=True)
        assert serializer.is_valid()

        for index, data in enumerate(serializer.validated_data):
            for key, value in data.items():
                assert value == updated_data_list[index][key]

        assert serializer.errors == []

    def test_as_field_allow_empty_true(self):
        class ListSerializer(serializers.Serializer):
            update_field = serializers.IntegerField()
            store_field = serializers.IntegerField()

        class Serializer(serializers.Serializer):
            extra_field = serializers.IntegerField()
            list_field = ListSerializer(many=True)

        instance = {
            'extra_field': 1,
            'list_field': [
                {'update_field': 11, 'store_field': 12},
                {'update_field': 21, 'store_field': 22},
            ]
        }

        serializer = Serializer(instance, data={}, partial=True)
        assert serializer.is_valid()
        assert serializer.validated_data == {}
        assert serializer.errors == {}

    def test_update_as_field_allow_empty_true(self):
        class ListSerializer(serializers.Serializer):
            update_field = serializers.IntegerField()
            store_field = serializers.IntegerField()

        class Serializer(serializers.Serializer):
            extra_field = serializers.IntegerField()
            list_field = ListSerializer(many=True)

        instance = {
            'extra_field': 1,
            'list_field': [
                {'update_field': 11, 'store_field': 12},
                {'update_field': 21, 'store_field': 22},
            ]
        }
        input_data_1 = {'extra_field': 2}
        input_data_2 = {
            'list_field': [
                {'update_field': 31},
                {'update_field': 41},
            ]
        }

        # data_1
        serializer = Serializer(instance, data=input_data_1, partial=True)
        assert serializer.is_valid()
        assert len(serializer.validated_data) == 1
        assert serializer.validated_data['extra_field'] == 2
        assert serializer.errors == {}

        # data_2
        serializer = Serializer(instance, data=input_data_2, partial=True)
        assert serializer.is_valid()

        updated_data_list = [
            {'update_field': 31, 'store_field': 12},
            {'update_field': 41, 'store_field': 22},
        ]
        for index, data in enumerate(serializer.validated_data['list_field']):
            for key, value in data.items():
                assert value == updated_data_list[index][key]

        assert serializer.errors == {}

    def test_as_field_allow_empty_false(self):
        class ListSerializer(serializers.Serializer):
            update_field = serializers.IntegerField()
            store_field = serializers.IntegerField()

        class Serializer(serializers.Serializer):
            extra_field = serializers.IntegerField()
            list_field = ListSerializer(many=True, allow_empty=False)

        instance = {
            'extra_field': 1,
            'list_field': [
                {'update_field': 11, 'store_field': 12},
                {'update_field': 21, 'store_field': 22},
            ]
        }

        serializer = Serializer(instance, data={}, partial=True)
        assert serializer.is_valid()
        assert serializer.validated_data == {}
        assert serializer.errors == {}

    def test_update_as_field_allow_empty_false(self):
        class ListSerializer(serializers.Serializer):
            update_field = serializers.IntegerField()
            store_field = serializers.IntegerField()

        class Serializer(serializers.Serializer):
            extra_field = serializers.IntegerField()
            list_field = ListSerializer(many=True, allow_empty=False)

        instance = {
            'extra_field': 1,
            'list_field': [
                {'update_field': 11, 'store_field': 12},
                {'update_field': 21, 'store_field': 22},
            ]
        }
        input_data_1 = {'extra_field': 2}
        input_data_2 = {
            'list_field': [
                {'update_field': 31},
                {'update_field': 41},
            ]
        }
        updated_data_list = [
            {'update_field': 31, 'store_field': 12},
            {'update_field': 41, 'store_field': 22},
        ]

        # data_1
        serializer = Serializer(instance, data=input_data_1, partial=True)
        assert serializer.is_valid()
        assert serializer.errors == {}

        # data_2
        serializer = Serializer(instance, data=input_data_2, partial=True)
        assert serializer.is_valid()

        for index, data in enumerate(serializer.validated_data['list_field']):
            for key, value in data.items():
                assert value == updated_data_list[index][key]

        assert serializer.errors == {}


class TestEmptyListSerializer:
    """
    Tests the behaviour of ListSerializers when there is no data passed to it
    """

    def setup_method(self):
        class ExampleListSerializer(serializers.ListSerializer):
            child = serializers.IntegerField()

        self.Serializer = ExampleListSerializer

    def test_nested_serializer_with_list_json(self):
        # pass an empty array to the serializer
        input_data = []

        serializer = self.Serializer(data=input_data)

        assert serializer.is_valid()
        assert serializer.validated_data == []

    def test_nested_serializer_with_list_multipart(self):
        # pass an "empty" QueryDict to the serializer (should be the same as an empty array)
        input_data = QueryDict('')
        serializer = self.Serializer(data=input_data)

        assert serializer.is_valid()
        assert serializer.validated_data == []


class TestMaxMinLengthListSerializer:
    """
    Tests the behaviour of ListSerializers when max_length and min_length are used
    """

    def setup_method(self):
        class IntegerSerializer(serializers.Serializer):
            some_int = serializers.IntegerField()

        class MaxLengthSerializer(serializers.Serializer):
            many_int = IntegerSerializer(many=True, max_length=5)

        class MinLengthSerializer(serializers.Serializer):
            many_int = IntegerSerializer(many=True, min_length=3)

        class MaxMinLengthSerializer(serializers.Serializer):
            many_int = IntegerSerializer(many=True, min_length=3, max_length=5)

        self.MaxLengthSerializer = MaxLengthSerializer
        self.MinLengthSerializer = MinLengthSerializer
        self.MaxMinLengthSerializer = MaxMinLengthSerializer

    def test_min_max_length_two_items(self):
        input_data = {'many_int': [{'some_int': i} for i in range(2)]}

        max_serializer = self.MaxLengthSerializer(data=input_data)
        min_serializer = self.MinLengthSerializer(data=input_data)
        max_min_serializer = self.MaxMinLengthSerializer(data=input_data)

        assert max_serializer.is_valid()
        assert max_serializer.validated_data == input_data

        assert not min_serializer.is_valid()

        assert not max_min_serializer.is_valid()

    def test_min_max_length_four_items(self):
        input_data = {'many_int': [{'some_int': i} for i in range(4)]}

        max_serializer = self.MaxLengthSerializer(data=input_data)
        min_serializer = self.MinLengthSerializer(data=input_data)
        max_min_serializer = self.MaxMinLengthSerializer(data=input_data)

        assert max_serializer.is_valid()
        assert max_serializer.validated_data == input_data

        assert min_serializer.is_valid()
        assert min_serializer.validated_data == input_data

        assert max_min_serializer.is_valid()
        assert min_serializer.validated_data == input_data

    def test_min_max_length_six_items(self):
        input_data = {'many_int': [{'some_int': i} for i in range(6)]}

        max_serializer = self.MaxLengthSerializer(data=input_data)
        min_serializer = self.MinLengthSerializer(data=input_data)
        max_min_serializer = self.MaxMinLengthSerializer(data=input_data)

        assert not max_serializer.is_valid()

        assert min_serializer.is_valid()
        assert min_serializer.validated_data == input_data

        assert not max_min_serializer.is_valid()


@pytest.mark.django_db()
class TestToRepresentationManagerCheck:
    """
    https://github.com/encode/django-rest-framework/issues/8726
    """

    def setup_method(self):
        class CustomManagerModelSerializer(serializers.ModelSerializer):
            class Meta:
                model = CustomManagerModel
                fields = '__all__'

        class OneToOneTargetSerializer(serializers.ModelSerializer):
            my_model = CustomManagerModelSerializer(many=True, source="custommanagermodel_set")

            class Meta:
                model = OneToOneTarget
                fields = '__all__'
                depth = 3

        class NullableOneToOneSourceSerializer(serializers.ModelSerializer):
            target = OneToOneTargetSerializer()

            class Meta:
                model = NullableOneToOneSource
                fields = '__all__'

        self.serializer = NullableOneToOneSourceSerializer

    def test(self):
        o2o_target = OneToOneTarget.objects.create(name='OneToOneTarget')
        NullableOneToOneSource.objects.create(
            name='NullableOneToOneSource',
            target=o2o_target
        )
        queryset = NullableOneToOneSource.objects.all()
        serializer = self.serializer(queryset, many=True)
        assert serializer.data
