import re

from django.shortcuts import render


def test_base_template_with_context():
    context = {'request': True, 'csrf_token': 'TOKEN'}
    result = render({}, 'rest_framework/base.html', context=context)
    assert re.search(r'"csrfToken": "TOKEN"', result.content.decode())


def test_base_template_with_no_context():
    # base.html should be renderable with no context,
    # so it can be easily extended.
    result = render({}, 'rest_framework/base.html')
    # note that this response will not include a valid CSRF token
    assert re.search(r'"csrfToken": ""', result.content.decode())
