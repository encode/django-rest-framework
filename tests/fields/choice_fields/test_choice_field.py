from django.http import QueryDict

from rest_framework import serializers

from ..base import FieldValues


class TestChoiceField(FieldValues):
    """
    Valid and invalid values for `ChoiceField`.
    """
    valid_inputs = {
        'poor': 'poor',
        'medium': 'medium',
        'good': 'good',
    }
    invalid_inputs = {
        'amazing': ['"amazing" is not a valid choice.']
    }
    outputs = {
        'good': 'good',
        '': '',
        'amazing': 'amazing',
    }
    field = serializers.ChoiceField(
        choices=[
            ('poor', 'Poor quality'),
            ('medium', 'Medium quality'),
            ('good', 'Good quality'),
        ]
    )

    def test_allow_blank(self):
        """
        If `allow_blank=True` then '' is a valid input.
        """
        field = serializers.ChoiceField(
            allow_blank=True,
            choices=[
                ('poor', 'Poor quality'),
                ('medium', 'Medium quality'),
                ('good', 'Good quality'),
            ]
        )
        output = field.run_validation('')
        assert output == ''

    def test_allow_null(self):
        """
        If `allow_null=True` then '' on HTML forms is treated as None.
        """
        field = serializers.ChoiceField(
            allow_null=True,
            choices=[
                1, 2, 3
            ]
        )
        field.field_name = 'example'
        value = field.get_value(QueryDict('example='))
        assert value is None
        output = field.run_validation(None)
        assert output is None

    def test_iter_options(self):
        """
        iter_options() should return a list of options and option groups.
        """
        field = serializers.ChoiceField(
            choices=[
                ('Numbers', ['integer', 'float']),
                ('Strings', ['text', 'email', 'url']),
                'boolean'
            ]
        )
        items = list(field.iter_options())

        assert items[0].start_option_group
        assert items[0].label == 'Numbers'
        assert items[1].value == 'integer'
        assert items[2].value == 'float'
        assert items[3].end_option_group

        assert items[4].start_option_group
        assert items[4].label == 'Strings'
        assert items[5].value == 'text'
        assert items[6].value == 'email'
        assert items[7].value == 'url'
        assert items[8].end_option_group

        assert items[9].value == 'boolean'


class TestChoiceFieldWithType(FieldValues):
    """
    Valid and invalid values for a `Choice` field that uses an integer type,
    instead of a char type.
    """
    valid_inputs = {
        '1': 1,
        3: 3,
    }
    invalid_inputs = {
        5: ['"5" is not a valid choice.'],
        'abc': ['"abc" is not a valid choice.']
    }
    outputs = {
        '1': 1,
        1: 1
    }
    field = serializers.ChoiceField(
        choices=[
            (1, 'Poor quality'),
            (2, 'Medium quality'),
            (3, 'Good quality'),
        ]
    )


class TestChoiceFieldWithListChoices(FieldValues):
    """
    Valid and invalid values for a `Choice` field that uses a flat list for the
    choices, rather than a list of pairs of (`value`, `description`).
    """
    valid_inputs = {
        'poor': 'poor',
        'medium': 'medium',
        'good': 'good',
    }
    invalid_inputs = {
        'awful': ['"awful" is not a valid choice.']
    }
    outputs = {
        'good': 'good'
    }
    field = serializers.ChoiceField(choices=('poor', 'medium', 'good'))


class TestChoiceFieldWithGroupedChoices(FieldValues):
    """
    Valid and invalid values for a `Choice` field that uses a grouped list for the
    choices, rather than a list of pairs of (`value`, `description`).
    """
    valid_inputs = {
        'poor': 'poor',
        'medium': 'medium',
        'good': 'good',
    }
    invalid_inputs = {
        'awful': ['"awful" is not a valid choice.']
    }
    outputs = {
        'good': 'good'
    }
    field = serializers.ChoiceField(
        choices=[
            (
                'Category',
                (
                    ('poor', 'Poor quality'),
                    ('medium', 'Medium quality'),
                ),
            ),
            ('good', 'Good quality'),
        ]
    )


class TestChoiceFieldWithMixedChoices(FieldValues):
    """
    Valid and invalid values for a `Choice` field that uses a single paired or
    grouped.
    """
    valid_inputs = {
        'poor': 'poor',
        'medium': 'medium',
        'good': 'good',
    }
    invalid_inputs = {
        'awful': ['"awful" is not a valid choice.']
    }
    outputs = {
        'good': 'good'
    }
    field = serializers.ChoiceField(
        choices=[
            (
                'Category',
                (
                    ('poor', 'Poor quality'),
                ),
            ),
            'medium',
            ('good', 'Good quality'),
        ]
    )
