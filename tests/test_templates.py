import re

from django.shortcuts import render


def test_base_template_with_no_context():
    # base.html should be renderable with no context,
    # so it can be easily extended.
    result = render({}, 'rest_framework/base.html')
    # note that this response will not include a valid CSRF token
    assert re.search(r'\bcsrfToken: ""', result.content.decode('utf-8'))
