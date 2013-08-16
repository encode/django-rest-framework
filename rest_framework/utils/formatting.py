"""
Utility functions to return a formatted name and description for a given view.
"""
from __future__ import unicode_literals

from django.utils.html import escape
from django.utils.safestring import mark_safe
from rest_framework.compat import apply_markdown, smart_text
import re
from rest_framework.settings import api_settings


def _remove_trailing_string(content, trailing):
    """
    Strip trailing component `trailing` from `content` if it exists.
    Used when generating names from view classes.
    """
    if content.endswith(trailing) and content != trailing:
        return content[:-len(trailing)]
    return content


def _remove_leading_indent(content):
    """
    Remove leading indent from a block of text.
    Used when generating descriptions from docstrings.
    """
    whitespace_counts = [len(line) - len(line.lstrip(' '))
                         for line in content.splitlines()[1:] if line.lstrip()]

    # unindent the content if needed
    if whitespace_counts:
        whitespace_pattern = '^' + (' ' * min(whitespace_counts))
        content = re.sub(re.compile(whitespace_pattern, re.MULTILINE), '', content)
    content = content.strip('\n')
    return content


def _camelcase_to_spaces(content):
    """
    Translate 'CamelCaseNames' to 'Camel Case Names'.
    Used when generating names from view classes.
    """
    camelcase_boundry = '(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))'
    content = re.sub(camelcase_boundry, ' \\1', content).strip()
    return ' '.join(content.split('_')).title()


def get_view_name(cls, suffix=None):
    """
    Return a formatted name for an `APIView` class or `@api_view` function.
    """
    return api_settings.VIEW_NAME_FUNCTION(cls, suffix)


def get_view_description(cls, html=False):
    """
    Return a description for an `APIView` class or `@api_view` function.
    """
    return api_settings.VIEW_DESCRIPTION_FUNCTION(cls)


def markup_description(description):
    """
    Apply HTML markup to the given description.
    """
    if apply_markdown:
        description = apply_markdown(description)
    else:
        description = escape(description).replace('\n', '<br />')
    return mark_safe(description)


def view_name(cls, suffix=None):
    name = cls.__name__
    name = _remove_trailing_string(name, 'View')
    name = _remove_trailing_string(name, 'ViewSet')
    name = _camelcase_to_spaces(name)
    if suffix:
        name += ' ' + suffix

    return name

def view_description(cls, html=False):
    description = cls.__doc__ or ''
    description = _remove_leading_indent(smart_text(description))
    if html:
        return markup_description(description)
    return description