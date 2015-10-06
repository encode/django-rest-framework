from __future__ import absolute_import, unicode_literals

import re

from django import template
from django.core.urlresolvers import NoReverseMatch, reverse
from django.template import Context, loader
from django.utils import six
from django.utils.encoding import force_text, iri_to_uri
from django.utils.html import escape, smart_urlquote
from django.utils.safestring import SafeData, mark_safe

from rest_framework.renderers import HTMLFormRenderer
from rest_framework.utils.urls import replace_query_param

register = template.Library()

# Regex for adding classes to html snippets
class_re = re.compile(r'(?<=class=["\'])(.*)(?=["\'])')


@register.simple_tag
def get_pagination_html(pager):
    return pager.to_html()


@register.simple_tag
def render_field(field, style=None):
    style = style or {}
    renderer = style.get('renderer', HTMLFormRenderer())
    return renderer.render_field(field, style)


@register.simple_tag
def optional_login(request):
    """
    Include a login snippet if REST framework's login view is in the URLconf.
    """
    try:
        login_url = reverse('rest_framework:login')
    except NoReverseMatch:
        return ''

    snippet = "<li><a href='{href}?next={next}'>Log in</a></li>"
    snippet = snippet.format(href=login_url, next=escape(request.path))
    return mark_safe(snippet)


@register.simple_tag
def optional_logout(request, user):
    """
    Include a logout snippet if REST framework's logout view is in the URLconf.
    """
    try:
        logout_url = reverse('rest_framework:logout')
    except NoReverseMatch:
        return '<li class="navbar-text">{user}</li>'.format(user=user)

    snippet = """<li class="dropdown">
        <a href="#" class="dropdown-toggle" data-toggle="dropdown">
            {user}
            <b class="caret"></b>
        </a>
        <ul class="dropdown-menu">
            <li><a href='{href}?next={next}'>Log out</a></li>
        </ul>
    </li>"""
    snippet = snippet.format(user=escape(user), href=logout_url, next=escape(request.path))
    return mark_safe(snippet)


@register.simple_tag
def add_query_param(request, key, val):
    """
    Add a query parameter to the current request url, and return the new url.
    """
    iri = request.get_full_path()
    uri = iri_to_uri(iri)
    return escape(replace_query_param(uri, key, val))


@register.filter
def add_class(value, css_class):
    """
    http://stackoverflow.com/questions/4124220/django-adding-css-classes-when-rendering-form-fields-in-a-template

    Inserts classes into template variables that contain HTML tags,
    useful for modifying forms without needing to change the Form objects.

    Usage:

        {{ field.label_tag|add_class:"control-label" }}

    In the case of REST Framework, the filter is used to add Bootstrap-specific
    classes to the forms.
    """
    html = six.text_type(value)
    match = class_re.search(html)
    if match:
        m = re.search(r'^%s$|^%s\s|\s%s\s|\s%s$' % (css_class, css_class,
                                                    css_class, css_class),
                      match.group(1))
        if not m:
            return mark_safe(class_re.sub(match.group(1) + " " + css_class,
                                          html))
    else:
        return mark_safe(html.replace('>', ' class="%s">' % css_class, 1))
    return value


@register.filter
def format_value(value):
    if getattr(value, 'is_hyperlink', False):
        return mark_safe('<a href=%s>%s</a>' % (value, escape(value.name)))
    if value is None or isinstance(value, bool):
        return mark_safe('<code>%s</code>' % {True: 'true', False: 'false', None: 'null'}[value])
    elif isinstance(value, list):
        if any([isinstance(item, (list, dict)) for item in value]):
            template = loader.get_template('rest_framework/admin/list_value.html')
        else:
            template = loader.get_template('rest_framework/admin/simple_list_value.html')
        context = Context({'value': value})
        return template.render(context)
    elif isinstance(value, dict):
        template = loader.get_template('rest_framework/admin/dict_value.html')
        context = Context({'value': value})
        return template.render(context)
    elif isinstance(value, six.string_types):
        if (
            (value.startswith('http:') or value.startswith('https:')) and not
            re.search(r'\s', value)
        ):
            return mark_safe('<a href="{value}">{value}</a>'.format(value=escape(value)))
        elif '@' in value and not re.search(r'\s', value):
            return mark_safe('<a href="mailto:{value}">{value}</a>'.format(value=escape(value)))
        elif '\n' in value:
            return mark_safe('<pre>%s</pre>' % escape(value))
    return six.text_type(value)


@register.filter
def add_nested_class(value):
    if isinstance(value, dict):
        return 'class=nested'
    if isinstance(value, list) and any([isinstance(item, (list, dict)) for item in value]):
        return 'class=nested'
    return ''


# Bunch of stuff cloned from urlize
TRAILING_PUNCTUATION = ['.', ',', ':', ';', '.)', '"', "']", "'}", "'"]
WRAPPING_PUNCTUATION = [('(', ')'), ('<', '>'), ('[', ']'), ('&lt;', '&gt;'),
                        ('"', '"'), ("'", "'")]
word_split_re = re.compile(r'(\s+)')
simple_url_re = re.compile(r'^https?://\[?\w', re.IGNORECASE)
simple_url_2_re = re.compile(r'^www\.|^(?!http)\w[^@]+\.(com|edu|gov|int|mil|net|org)$', re.IGNORECASE)
simple_email_re = re.compile(r'^\S+@\S+\.\S+$')


def smart_urlquote_wrapper(matched_url):
    """
    Simple wrapper for smart_urlquote. ValueError("Invalid IPv6 URL") can
    be raised here, see issue #1386
    """
    try:
        return smart_urlquote(matched_url)
    except ValueError:
        return None


@register.filter
def urlize_quoted_links(text, trim_url_limit=None, nofollow=True, autoescape=True):
    """
    Converts any URLs in text into clickable links.

    Works on http://, https://, www. links, and also on links ending in one of
    the original seven gTLDs (.com, .edu, .gov, .int, .mil, .net, and .org).
    Links can have trailing punctuation (periods, commas, close-parens) and
    leading punctuation (opening parens) and it'll still do the right thing.

    If trim_url_limit is not None, the URLs in link text longer than this limit
    will truncated to trim_url_limit-3 characters and appended with an elipsis.

    If nofollow is True, the URLs in link text will get a rel="nofollow"
    attribute.

    If autoescape is True, the link text and URLs will get autoescaped.
    """
    def trim_url(x, limit=trim_url_limit):
        return limit is not None and (len(x) > limit and ('%s...' % x[:max(0, limit - 3)])) or x

    safe_input = isinstance(text, SafeData)
    words = word_split_re.split(force_text(text))
    for i, word in enumerate(words):
        if '.' in word or '@' in word or ':' in word:
            # Deal with punctuation.
            lead, middle, trail = '', word, ''
            for punctuation in TRAILING_PUNCTUATION:
                if middle.endswith(punctuation):
                    middle = middle[:-len(punctuation)]
                    trail = punctuation + trail
            for opening, closing in WRAPPING_PUNCTUATION:
                if middle.startswith(opening):
                    middle = middle[len(opening):]
                    lead = lead + opening
                # Keep parentheses at the end only if they're balanced.
                if (
                    middle.endswith(closing) and
                    middle.count(closing) == middle.count(opening) + 1
                ):
                    middle = middle[:-len(closing)]
                    trail = closing + trail

            # Make URL we want to point to.
            url = None
            nofollow_attr = ' rel="nofollow"' if nofollow else ''
            if simple_url_re.match(middle):
                url = smart_urlquote_wrapper(middle)
            elif simple_url_2_re.match(middle):
                url = smart_urlquote_wrapper('http://%s' % middle)
            elif ':' not in middle and simple_email_re.match(middle):
                local, domain = middle.rsplit('@', 1)
                try:
                    domain = domain.encode('idna').decode('ascii')
                except UnicodeError:
                    continue
                url = 'mailto:%s@%s' % (local, domain)
                nofollow_attr = ''

            # Make link.
            if url:
                trimmed = trim_url(middle)
                if autoescape and not safe_input:
                    lead, trail = escape(lead), escape(trail)
                    url, trimmed = escape(url), escape(trimmed)
                middle = '<a href="%s"%s>%s</a>' % (url, nofollow_attr, trimmed)
                words[i] = mark_safe('%s%s%s' % (lead, middle, trail))
            else:
                if safe_input:
                    words[i] = mark_safe(word)
                elif autoescape:
                    words[i] = escape(word)
        elif safe_input:
            words[i] = mark_safe(word)
        elif autoescape:
            words[i] = escape(word)
    return ''.join(words)


@register.filter
def break_long_headers(header):
    """
    Breaks headers longer than 160 characters (~page length)
    when possible (are comma separated)
    """
    if len(header) > 160 and ',' in header:
        header = mark_safe('<br> ' + ', <br>'.join(header.split(',')))
    return header
