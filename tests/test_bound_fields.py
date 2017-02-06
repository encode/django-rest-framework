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

    def test_delete_field(self):
        class ExampleSerializer(serializers.Serializer):
            text = serializers.CharField(max_length=100)
            amount = serializers.IntegerField()

        serializer = ExampleSerializer()
        del serializer.fields['text']
        assert 'text' not in serializer.fields.keys()

    def test_as_form_fields(self):
        class ExampleSerializer(serializers.Serializer):
            bool_field = serializers.BooleanField()
            null_field = serializers.IntegerField(allow_null=True)

        serializer = ExampleSerializer(data={'bool_field': False, 'null_field': None})
        assert serializer.is_valid()
        assert serializer['bool_field'].as_form_field().value == ''
        assert serializer['null_field'].as_form_field().value == ''

    def test_rendering_boolean_field(self):
        from rest_framework.renderers import HTMLFormRenderer

        class ExampleSerializer(serializers.Serializer):
            bool_field = serializers.BooleanField(
                style={'base_template': 'checkbox.html', 'template_pack': 'rest_framework/vertical'})

        serializer = ExampleSerializer(data={'bool_field': True})
        assert serializer.is_valid()
        renderer = HTMLFormRenderer()
        rendered = renderer.render_field(serializer['bool_field'], {})
        expected_packed = (
            '<divclass="form-group">'
            '<divclass="checkbox">'
            '<label>'
            '<inputtype="checkbox"name="bool_field"value="true"checked>'
            'Boolfield'
            '</label>'
            '</div>'
            '</div>'
        )
        rendered_packed = ''.join(rendered.split())
        assert rendered_packed == expected_packed


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

    def test_as_form_fields(self):
        class Nested(serializers.Serializer):
            bool_field = serializers.BooleanField()
            null_field = serializers.IntegerField(allow_null=True)

        class ExampleSerializer(serializers.Serializer):
            nested = Nested()

        serializer = ExampleSerializer(data={'nested': {'bool_field': False, 'null_field': None}})
        assert serializer.is_valid()
        assert serializer['nested']['bool_field'].as_form_field().value == ''
        assert serializer['nested']['null_field'].as_form_field().value == ''

    def test_rendering_nested_fields_with_none_value(self):
        from rest_framework.renderers import HTMLFormRenderer

        class Nested1(serializers.Serializer):
            text_field = serializers.CharField()

        class Nested2(serializers.Serializer):
            nested1 = Nested1(allow_null=True)
            text_field = serializers.CharField()

        class ExampleSerializer(serializers.Serializer):
            nested2 = Nested2()

        serializer = ExampleSerializer(data={'nested2': {'nested1': None, 'text_field': 'test'}})
        assert serializer.is_valid()
        renderer = HTMLFormRenderer()
        for field in serializer:
            rendered = renderer.render_field(field, {})
            expected_packed = (
                '<fieldset>'
                '<legend>Nested2</legend>'
                '<fieldset>'
                '<legend>Nested1</legend>'
                '<divclass="form-group">'
                '<label>Textfield</label>'
                '<inputname="nested2.nested1.text_field"class="form-control"type="text">'
                '</div>'
                '</fieldset>'
                '<divclass="form-group">'
                '<label>Textfield</label>'
                '<inputname="nested2.text_field"class="form-control"type="text"value="test">'
                '</div>'
                '</fieldset>'
            )
            rendered_packed = ''.join(rendered.split())
            assert rendered_packed == expected_packed
