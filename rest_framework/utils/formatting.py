"""
Utility functions to return a formatted name and description for a given view.
"""
from __future__ import unicode_literals

import re

from django.utils.encoding import force_text
from django.utils.html import escape
from django.utils.safestring import mark_safe

from rest_framework.compat import apply_markdown


def remove_trailing_string(content, trailing):
    """
    Strip trailing component `trailing` from `content` if it exists.
    Used when generating names from view classes.
    """
    if content.endswith(trailing) and content != trailing:
        return content[:-len(trailing)]
    return content


def dedent(content):
    """
    Remove leading indent from a block of text.
    Used when generating descriptions from docstrings.

    Note that python's `textwrap.dedent` doesn't quite cut it,
    as it fails to dedent multiline docstrings that include
    unindented text on the initial line.
    """
    content = force_text(content)
    whitespace_counts = [
        len(line) - len(line.lstrip(' '))
        for line in content.splitlines()[1:] if line.lstrip()
    ]
    tab_counts = [
        len(line) - len(line.lstrip('\t'))
        for line in content.splitlines()[1:] if line.lstrip()
    ]

    # unindent the content if needed
    if whitespace_counts:
        whitespace_pattern = '^' + (' ' * min(whitespace_counts))
        content = re.sub(re.compile(whitespace_pattern, re.MULTILINE), '', content)
    elif tab_counts:
        whitespace_pattern = '^' + ('\t' * min(whitespace_counts))
        content = re.sub(re.compile(whitespace_pattern, re.MULTILINE), '', content)

    return content.strip()


def camelcase_to_spaces(content):
    """
    Translate 'CamelCaseNames' to 'Camel Case Names'.
    Used when generating names from view classes.
    """
    camelcase_boundry = '(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))'
    content = re.sub(camelcase_boundry, ' \\1', content).strip()
    return ' '.join(content.split('_')).title()


def markup_description(description):
    """
    Apply HTML markup to the given description.
    """
    if apply_markdown:
        description = apply_markdown(description)
    else:
        description = escape(description).replace('\n', '<br />')
        description = '<p>' + description + '</p>'
    return mark_safe(description)
