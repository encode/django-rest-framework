import pytest

from rest_framework import serializers


class TestEmpty:
    """
    Tests for `required`, `allow_null`, `allow_blank`, `default`.
    """

    def test_required(self):
        """
        By default a field must be included in the input.
        """
        field = serializers.IntegerField()
        with pytest.raises(serializers.ValidationError) as exc_info:
            field.run_validation()
        assert exc_info.value.detail == ['This field is required.']

    def test_not_required(self):
        """
        If `required=False` then a field may be omitted from the input.
        """
        field = serializers.IntegerField(required=False)
        with pytest.raises(serializers.SkipField):
            field.run_validation()

    def test_disallow_null(self):
        """
        By default `None` is not a valid input.
        """
        field = serializers.IntegerField()
        with pytest.raises(serializers.ValidationError) as exc_info:
            field.run_validation(None)
        assert exc_info.value.detail == ['This field may not be null.']

    def test_allow_null(self):
        """
        If `allow_null=True` then `None` is a valid input.
        """
        field = serializers.IntegerField(allow_null=True)
        output = field.run_validation(None)
        assert output is None

    def test_disallow_blank(self):
        """
        By default '' is not a valid input.
        """
        field = serializers.CharField()
        with pytest.raises(serializers.ValidationError) as exc_info:
            field.run_validation('')
        assert exc_info.value.detail == ['This field may not be blank.']

    def test_allow_blank(self):
        """
        If `allow_blank=True` then '' is a valid input.
        """
        field = serializers.CharField(allow_blank=True)
        output = field.run_validation('')
        assert output == ''

    def test_default(self):
        """
        If `default` is set, then omitted values get the default input.
        """
        field = serializers.IntegerField(default=123)
        output = field.run_validation()
        assert output is 123


class TestSource:
    def test_source(self):
        class ExampleSerializer(serializers.Serializer):
            example_field = serializers.CharField(source='other')

        serializer = ExampleSerializer(data={'example_field': 'abc'})
        assert serializer.is_valid()
        assert serializer.validated_data == {'other': 'abc'}

    def test_redundant_source(self):
        class ExampleSerializer(serializers.Serializer):
            example_field = serializers.CharField(source='example_field')

        with pytest.raises(AssertionError) as exc_info:
            ExampleSerializer().fields
        assert str(exc_info.value) == (
            "It is redundant to specify `source='example_field'` on field "
            "'CharField' in serializer 'ExampleSerializer', because it is the "
            "same as the field name. Remove the `source` keyword argument."
        )

    def test_callable_source(self):
        class ExampleSerializer(serializers.Serializer):
            example_field = serializers.CharField(source='example_callable')

        class ExampleInstance(object):
            def example_callable(self):
                return 'example callable value'

        serializer = ExampleSerializer(ExampleInstance())
        assert serializer.data['example_field'] == 'example callable value'

    def test_callable_source_raises(self):
        class ExampleSerializer(serializers.Serializer):
            example_field = serializers.CharField(source='example_callable', read_only=True)

        class ExampleInstance(object):
            def example_callable(self):
                raise AttributeError('method call failed')

        with pytest.raises(ValueError) as exc_info:
            serializer = ExampleSerializer(ExampleInstance())
            serializer.data.items()

        assert 'method call failed' in str(exc_info.value)


class TestReadOnly:
    def setup(self):
        class TestSerializer(serializers.Serializer):
            read_only = serializers.ReadOnlyField()
            writable = serializers.IntegerField()

        self.Serializer = TestSerializer

    def test_validate_read_only(self):
        """
        Read-only serializers.should not be included in validation.
        """
        data = {'read_only': 123, 'writable': 456}
        serializer = self.Serializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data == {'writable': 456}

    def test_serialize_read_only(self):
        """
        Read-only serializers.should be serialized.
        """
        instance = {'read_only': 123, 'writable': 456}
        serializer = self.Serializer(instance)
        assert serializer.data == {'read_only': 123, 'writable': 456}


class TestWriteOnly:
    def setup(self):
        class TestSerializer(serializers.Serializer):
            write_only = serializers.IntegerField(write_only=True)
            readable = serializers.IntegerField()

        self.Serializer = TestSerializer

    def test_validate_write_only(self):
        """
        Write-only serializers.should be included in validation.
        """
        data = {'write_only': 123, 'readable': 456}
        serializer = self.Serializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data == {'write_only': 123, 'readable': 456}

    def test_serialize_write_only(self):
        """
        Write-only serializers.should not be serialized.
        """
        instance = {'write_only': 123, 'readable': 456}
        serializer = self.Serializer(instance)
        assert serializer.data == {'readable': 456}


class TestInitial:
    def setup(self):
        class TestSerializer(serializers.Serializer):
            initial_field = serializers.IntegerField(initial=123)
            blank_field = serializers.IntegerField()

        self.serializer = TestSerializer()

    def test_initial(self):
        """
        Initial values should be included when serializing a new representation.
        """
        assert self.serializer.data == {
            'initial_field': 123,
            'blank_field': None
        }


class TestInitialWithCallable:
    def setup(self):
        def initial_value():
            return 123

        class TestSerializer(serializers.Serializer):
            initial_field = serializers.IntegerField(initial=initial_value)

        self.serializer = TestSerializer()

    def test_initial_should_accept_callable(self):
        """
        Follows the default ``Field.initial`` behaviour where they accept a
        callable to produce the initial value"""
        assert self.serializer.data == {
            'initial_field': 123,
        }


class TestLabel:
    def setup(self):
        class TestSerializer(serializers.Serializer):
            labeled = serializers.IntegerField(label='My label')

        self.serializer = TestSerializer()

    def test_label(self):
        """
        A field's label may be set with the `label` argument.
        """
        fields = self.serializer.fields
        assert fields['labeled'].label == 'My label'
