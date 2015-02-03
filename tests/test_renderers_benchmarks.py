from decimal import Decimal
from datetime import datetime

from pytest import mark

from rest_framework import renderers


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


@mark.bench('renderers.JSONRenderer.render', iterations=1000000)
def test_json_renderer():
    renderer = renderers.JSONRenderer()
    renderer.render(data)
