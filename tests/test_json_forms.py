from django.utils.datastructures import MultiValueDict

from rest_framework.utils import html


class TestHtmlJsonExamples:
    """
    Tests for the HTML JSON form algorithm
    Examples 1-10 from http://www.w3.org/TR/html-json-forms/
    """

    def test_basic_keys(self):
        """
        Example 1: Basic Keys
        """
        input_data = {
            'name': "Bender",
            'hind': "Bitable",
            'shiny': True
        }
        expected_output = input_data
        result = html.parse_json_form(input_data)
        assert result == expected_output

    def test_multiple_values(self):
        """
        Example 2: Multiple Values
        """
        input_data = MultiValueDict()
        input_data.setlist('bottle-on-wall', [1, 2, 3])
        expected_output = {
            'bottle-on-wall': [1, 2, 3]
        }
        result = html.parse_json_form(input_data)
        assert result == expected_output

    def test_deeper_structure(self):
        """
        Example 3: Deeper Structure
        """
        input_data = {
            'pet[species]': "Dahut",
            'pet[name]': "Hypatia",
            'kids[1]': "Thelma",
            'kids[0]': "Ashley",
        }
        expected_output = {
            'pet': {
                'species': "Dahut",
                'name': "Hypatia",
            },
            'kids': ["Ashley", "Thelma"],
        }
        result = html.parse_json_form(input_data)
        assert result == expected_output

    def test_sparse_arrays(self):
        """
        Example 4: Sparse Arrays
        """
        input_data = {
            "hearbeat[0]": "thunk",
            "hearbeat[2]": "thunk",
        }
        expected_output = {
            "hearbeat": ["thunk", None, "thunk"]
        }
        result = html.parse_json_form(input_data)
        assert result == expected_output

    def test_even_deeper(self):
        """
        Example 5: Even Deeper
        """
        input_data = {
            'pet[0][species]': "Dahut",
            'pet[0][name]': "Hypatia",
            'pet[1][species]': "Felis Stultus",
            'pet[1][name]': "Billie",
        }
        expected_output = {
            'pet': [
                {
                    'species': "Dahut",
                    'name': "Hypatia",
                },
                {
                    'species': "Felis Stultus",
                    'name': "Billie",
                }
            ]
        }
        result = html.parse_json_form(input_data)
        assert result == expected_output

    def test_such_deep(self):
        """
        Example 6: Such Deep
        """
        input_data = {
            'wow[such][deep][3][much][power][!]': "Amaze",
        }
        expected_output = {
            'wow': {
                'such': {
                    'deep': [
                        None,
                        None,
                        None,
                        {
                            'much': {
                                'power': {
                                    '!': "Amaze",
                                }
                            }
                        }
                    ]
                }
            }
        }
        result = html.parse_json_form(input_data)
        assert result == expected_output

    def test_merge_behaviour(self):
        """
        Example 7: Merge Behaviour
        """
        # FIXME: Shouldn't this work regardless of key order?
        from rest_framework.compat import OrderedDict
        input_data = OrderedDict([
            ('mix', "scalar"),
            ('mix[0]', "array 1"),
            ('mix[2]', "array 2"),
            ('mix[key]', "key key"),
            ('mix[car]', "car key"),
        ])
        expected_output = {
            'mix': {
                '': "scalar",
                '0': "array 1",
                '2': "array 2",
                'key': "key key",
                'car': "car key",
            }
        }
        result = html.parse_json_form(input_data)
        assert result == expected_output

    def test_append(self):
        """
        Example 8: Append
        """
        input_data = {
            'highlander[]': "one",
        }
        expected_output = {
            'highlander': ["one"],
        }
        result = html.parse_json_form(input_data)
        assert result == expected_output

    # TODO: Example 9: Files

    def test_invalid(self):
        """
        Example 10: Invalid
        """
        input_data = {
            "error[good]": "BOOM!",
            "error[bad": "BOOM BOOM!",
        }
        expected_output = {
            'error': {
                'good': "BOOM!",
            },
            'error[bad': "BOOM BOOM!",
        }
        result = html.parse_json_form(input_data)
        assert result == expected_output
