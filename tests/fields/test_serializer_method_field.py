import pytest

from rest_framework import serializers


# Tests for SerializerMethodField.
# --------------------------------
class TestSerializerMethodField:
    def test_serializer_method_field(self):
        class ExampleSerializer(serializers.Serializer):
            example_field = serializers.SerializerMethodField()

            def get_example_field(self, obj):
                return 'ran get_example_field(%d)' % obj['example_field']

        serializer = ExampleSerializer({'example_field': 123})
        assert serializer.data == {
            'example_field': 'ran get_example_field(123)'
        }

    def test_redundant_method_name(self):
        class ExampleSerializer(serializers.Serializer):
            example_field = serializers.SerializerMethodField('get_example_field')

        with pytest.raises(AssertionError) as exc_info:
            ExampleSerializer().fields
        assert str(exc_info.value) == (
            "It is redundant to specify `get_example_field` on "
            "SerializerMethodField 'example_field' in serializer "
            "'ExampleSerializer', because it is the same as the default "
            "method name. Remove the `method_name` argument."
        )
