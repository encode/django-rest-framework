from django.shortcuts import render


def test_base_template_with_no_context():
    # base.html should be renderable with no context,
    # so it can be easily extended.
    render({}, 'rest_framework/base.html')
