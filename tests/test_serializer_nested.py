from rest_framework import serializers


class TestNestedSerializer:
    def setup(self):
        class NestedSerializer(serializers.Serializer):
            one = serializers.IntegerField(max_value=10)
            two = serializers.IntegerField(max_value=10)

        class TestSerializer(serializers.Serializer):
            nested = NestedSerializer()

        self.Serializer = TestSerializer

    def test_nested_validate(self):
        input_data = {
            'nested': {
                'one': '1',
                'two': '2',
            }
        }
        expected_data = {
            'nested': {
                'one': 1,
                'two': 2,
            }
        }
        serializer = self.Serializer(data=input_data)
        assert serializer.is_valid()
        assert serializer.validated_data == expected_data

    def test_nested_serialize_empty(self):
        expected_data = {
            'nested': {
                'one': None,
                'two': None
            }
        }
        serializer = self.Serializer()
        assert serializer.data == expected_data


class TestNotRequiredNestedSerializer:
    def setup(self):
        class NestedSerializer(serializers.Serializer):
            one = serializers.IntegerField(max_value=10)

        class TestSerializer(serializers.Serializer):
            nested = NestedSerializer(required=False)

        self.Serializer = TestSerializer

        class FakeMultiDict(dict):
            """
            Use this to fake a `format="multipart"` request, because
            `utils.is_html_input()` returns `True` when the dict object has
            an attribute of "getlist".
            """
            def getlist(self, value, default=None):
                if value in self:
                    return [self[value]]
                else:
                    return [] if default is None else default

        self.FakeMultiDict = FakeMultiDict

    def test_json_validate(self):
        input_data = {}
        serializer = self.Serializer(data=input_data)
        assert serializer.is_valid()

        input_data = {'nested': {'one': '1'}}
        serializer = self.Serializer(data=input_data)
        assert serializer.is_valid()

    def test_multipart_validate(self):
        input_data = self.FakeMultiDict()
        serializer = self.Serializer(data=input_data)
        assert serializer.is_valid()

        input_data = self.FakeMultiDict(**{'nested.one': '1'})
        serializer = self.Serializer(data=input_data)
        assert serializer.is_valid()
