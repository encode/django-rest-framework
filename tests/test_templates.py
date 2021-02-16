import re

from django.shortcuts import render


def test_base_template_with_no_context():
    # base.html should be renderable with no context,
    # so it can be easily extended.
    result = render({}, 'rest_framework/base.html')
    # note that this response will not include a valid CSRF token
    assert re.search(r'\bcsrfToken: ""', result.content.decode())


def test_base_template_with_simple_context():
    context = {'request': True, 'csrf_token': 'TOKEN'}
    result = render({}, 'rest_framework/base.html', context=context)
    # note that response will STILL not include a CSRF token
    assert re.search(r'\bcsrfToken: ""', result.content.decode())


def test_base_template_with_editing_context():
    context = {'request': True, 'post_form': object(), 'csrf_token': 'TOKEN'}
    result = render({}, 'rest_framework/base.html', context=context)
    # response includes a CSRF token in support of the POST form
    assert re.search(r'\bcsrfToken: "TOKEN"', result.content.decode())
