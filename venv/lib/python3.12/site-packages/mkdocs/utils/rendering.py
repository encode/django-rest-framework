from __future__ import annotations

import copy
from typing import TYPE_CHECKING, Callable

import markdown
import markdown.treeprocessors

if TYPE_CHECKING:
    from xml.etree import ElementTree as etree

# TODO: This will become unnecessary after min-versions have Markdown >=3.4
_unescape: Callable[[str], str]
try:
    _unescape = markdown.treeprocessors.UnescapeTreeprocessor().unescape
except AttributeError:
    _unescape = lambda s: s

# TODO: Most of this file will become unnecessary after https://github.com/Python-Markdown/markdown/pull/1441


def get_heading_text(el: etree.Element, md: markdown.Markdown) -> str:
    el = copy.deepcopy(el)
    _remove_anchorlink(el)
    _remove_fnrefs(el)
    _extract_alt_texts(el)
    return _strip_tags(_render_inner_html(el, md))


def _strip_tags(text: str) -> str:
    """Strip HTML tags and return plain text. Note: HTML entities are unaffected."""
    # A comment could contain a tag, so strip comments first
    while (start := text.find('<!--')) != -1 and (end := text.find('-->', start)) != -1:
        text = text[:start] + text[end + 3 :]

    while (start := text.find('<')) != -1 and (end := text.find('>', start)) != -1:
        text = text[:start] + text[end + 1 :]

    # Collapse whitespace
    text = ' '.join(text.split())
    return text


def _render_inner_html(el: etree.Element, md: markdown.Markdown) -> str:
    # The `UnescapeTreeprocessor` runs after `toc` extension so run here.
    text = md.serializer(el)
    text = _unescape(text)

    # Strip parent tag
    start = text.index('>') + 1
    end = text.rindex('<')
    text = text[start:end].strip()

    for pp in md.postprocessors:
        text = pp.run(text)
    return text


def _remove_anchorlink(el: etree.Element) -> None:
    """Drop anchorlink from the element, if present."""
    if len(el) > 0 and el[-1].tag == 'a' and el[-1].get('class') == 'headerlink':
        del el[-1]


def _remove_fnrefs(root: etree.Element) -> None:
    """Remove footnote references from the element, if any are present."""
    for parent in root.findall('.//sup[@id]/..'):
        _replace_elements_with_text(parent, _predicate_for_fnrefs)


def _predicate_for_fnrefs(el: etree.Element) -> str | None:
    if el.tag == 'sup' and el.get('id', '').startswith('fnref'):
        return ''
    return None


def _extract_alt_texts(root: etree.Element) -> None:
    """For images that have an `alt` attribute, replace them with this content."""
    for parent in root.findall('.//img[@alt]/..'):
        _replace_elements_with_text(parent, _predicate_for_alt_texts)


def _predicate_for_alt_texts(el: etree.Element) -> str | None:
    if el.tag == 'img' and (alt := el.get('alt')):
        return alt
    return None


def _replace_elements_with_text(
    parent: etree.Element, predicate: Callable[[etree.Element], str | None]
) -> None:
    """For each child element, if matched, replace it with the text returned from the predicate."""
    carry_text = ""
    for child in reversed(parent):  # Reversed for the ability to mutate during iteration.
        # Remove matching elements but carry any `tail` text to preceding elements.
        new_text = predicate(child)
        if new_text is not None:
            carry_text = new_text + (child.tail or "") + carry_text
            parent.remove(child)
        elif carry_text:
            child.tail = (child.tail or "") + carry_text
            carry_text = ""
    if carry_text:
        parent.text = (parent.text or "") + carry_text
