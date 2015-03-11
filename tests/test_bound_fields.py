from rest_framework import serializers


class TestSimpleBoundField:
    def test_empty_bound_field(self):
        class ExampleSerializer(serializers.Serializer):
            text = serializers.CharField(max_length=100)
            amount = serializers.IntegerField()

        serializer = ExampleSerializer()

        assert serializer['text'].value == ''
        assert serializer['text'].errors is None
        assert serializer['text'].name == 'text'
        assert serializer['amount'].value is None
        assert serializer['amount'].errors is None
        assert serializer['amount'].name == 'amount'

    def test_populated_bound_field(self):
        class ExampleSerializer(serializers.Serializer):
            text = serializers.CharField(max_length=100)
            amount = serializers.IntegerField()

        serializer = ExampleSerializer(data={'text': 'abc', 'amount': 123})
        assert serializer.is_valid()
        assert serializer['text'].value == 'abc'
        assert serializer['text'].errors is None
        assert serializer['text'].name == 'text'
        assert serializer['amount'].value is 123
        assert serializer['amount'].errors is None
        assert serializer['amount'].name == 'amount'

    def test_error_bound_field(self):
        class ExampleSerializer(serializers.Serializer):
            text = serializers.CharField(max_length=100)
            amount = serializers.IntegerField()

        serializer = ExampleSerializer(data={'text': 'x' * 1000, 'amount': 123})
        serializer.is_valid()

        assert serializer['text'].value == 'x' * 1000
        assert serializer['text'].errors == ['Ensure this field has no more than 100 characters.']
        assert serializer['text'].name == 'text'
        assert serializer['amount'].value is 123
        assert serializer['amount'].errors is None
        assert serializer['amount'].name == 'amount'


class TestNestedBoundField:
    def test_nested_empty_bound_field(self):
        class Nested(serializers.Serializer):
            more_text = serializers.CharField(max_length=100)
            amount = serializers.IntegerField()

        class ExampleSerializer(serializers.Serializer):
            text = serializers.CharField(max_length=100)
            nested = Nested()

        serializer = ExampleSerializer()

        assert serializer['text'].value == ''
        assert serializer['text'].errors is None
        assert serializer['text'].name == 'text'
        assert serializer['nested']['more_text'].value == ''
        assert serializer['nested']['more_text'].errors is None
        assert serializer['nested']['more_text'].name == 'nested.more_text'
        assert serializer['nested']['amount'].value is None
        assert serializer['nested']['amount'].errors is None
        assert serializer['nested']['amount'].name == 'nested.amount'
