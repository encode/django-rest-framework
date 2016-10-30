from django.http import QueryDict

from rest_framework import serializers

from .base import FieldValues


class TestJSONField(FieldValues):
    """
    Values for `JSONField`.
    """
    valid_inputs = [
        ({
            'a': 1,
            'b': ['some', 'list', True, 1.23],
            '3': None
        }, {
            'a': 1,
            'b': ['some', 'list', True, 1.23],
            '3': None
        }),
    ]
    invalid_inputs = [
        ({'a': set()}, ['Value must be valid JSON.']),
    ]
    outputs = [
        ({
            'a': 1,
            'b': ['some', 'list', True, 1.23],
            '3': 3
        }, {
            'a': 1,
            'b': ['some', 'list', True, 1.23],
            '3': 3
        }),
    ]
    field = serializers.JSONField()

    def test_html_input_as_json_string(self):
        """
        HTML inputs should be treated as a serialized JSON string.
        """
        class TestSerializer(serializers.Serializer):
            config = serializers.JSONField()

        data = QueryDict(mutable=True)
        data.update({'config': '{"a":1}'})
        serializer = TestSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data == {'config': {"a": 1}}


class TestBinaryJSONField(FieldValues):
    """
    Values for `JSONField` with binary=True.
    """
    valid_inputs = [
        (b'{"a": 1, "3": null, "b": ["some", "list", true, 1.23]}', {
            'a': 1,
            'b': ['some', 'list', True, 1.23],
            '3': None
        }),
    ]
    invalid_inputs = [
        ('{"a": "unterminated string}', ['Value must be valid JSON.']),
    ]
    outputs = [
        (['some', 'list', True, 1.23], b'["some", "list", true, 1.23]'),
    ]
    field = serializers.JSONField(binary=True)
