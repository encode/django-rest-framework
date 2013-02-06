from __future__ import unicode_literals, absolute_import
from django import template
from django.core.urlresolvers import reverse, NoReverseMatch
from django.http import QueryDict
from django.utils.html import escape
from django.utils.safestring import SafeData, mark_safe
from rest_framework.compat import urlparse
from rest_framework.compat import force_text
from rest_framework.compat import six
import re
import string

register = template.Library()


# Note we don't use 'load staticfiles', because we need a 1.3 compatible
# version, so instead we include the `static` template tag ourselves.

# When 1.3 becomes unsupported by REST framework, we can instead start to
# use the {% load staticfiles %} tag, remove the following code,
# and add a dependancy that `django.contrib.staticfiles` must be installed.

# Note: We can't put this into the `compat` module because the compat import
# from rest_framework.compat import ...
# conflicts with this rest_framework template tag module.

try:  # Django 1.5+
    from django.contrib.staticfiles.templatetags.staticfiles import StaticFilesNode

    @register.tag('static')
    def do_static(parser, token):
        return StaticFilesNode.handle_token(parser, token)

except ImportError:
    try:  # Django 1.4
        from django.contrib.staticfiles.storage import staticfiles_storage

        @register.simple_tag
        def static(path):
            """
            A template tag that returns the URL to a file
            using staticfiles' storage backend
            """
            return staticfiles_storage.url(path)

    except ImportError:  # Django 1.3
        from urlparse import urljoin
        from django import template
        from django.templatetags.static import PrefixNode

        class StaticNode(template.Node):
            def __init__(self, varname=None, path=None):
                if path is None:
                    raise template.TemplateSyntaxError(
                        "Static template nodes must be given a path to return.")
                self.path = path
                self.varname = varname

            def url(self, context):
                path = self.path.resolve(context)
                return self.handle_simple(path)

            def render(self, context):
                url = self.url(context)
                if self.varname is None:
                    return url
                context[self.varname] = url
                return ''

            @classmethod
            def handle_simple(cls, path):
                return urljoin(PrefixNode.handle_simple("STATIC_URL"), path)

            @classmethod
            def handle_token(cls, parser, token):
                """
                Class method to parse prefix node and return a Node.
                """
                bits = token.split_contents()

                if len(bits) < 2:
                    raise template.TemplateSyntaxError(
                        "'%s' takes at least one argument (path to file)" % bits[0])

                path = parser.compile_filter(bits[1])

                if len(bits) >= 2 and bits[-2] == 'as':
                    varname = bits[3]
                else:
                    varname = None

                return cls(varname, path)

        @register.tag('static')
        def do_static_13(parser, token):
            return StaticNode.handle_token(parser, token)


def replace_query_param(url, key, val):
    """
    Given a URL and a key/val pair, set or replace an item in the query
    parameters of the URL, and return the new URL.
    """
    (scheme, netloc, path, query, fragment) = urlparse.urlsplit(url)
    query_dict = QueryDict(query).copy()
    query_dict[key] = val
    query = query_dict.urlencode()
    return urlparse.urlunsplit((scheme, netloc, path, query, fragment))


# Regex for adding classes to html snippets
class_re = re.compile(r'(?<=class=["\'])(.*)(?=["\'])')


# Bunch of stuff cloned from urlize
LEADING_PUNCTUATION = ['(', '<', '&lt;', '"', "'"]
TRAILING_PUNCTUATION = ['.', ',', ')', '>', '\n', '&gt;', '"', "'"]
DOTS = ['&middot;', '*', '\xe2\x80\xa2', '&#149;', '&bull;', '&#8226;']
unencoded_ampersands_re = re.compile(r'&(?!(\w+|#\d+);)')
word_split_re = re.compile(r'(\s+)')
punctuation_re = re.compile('^(?P<lead>(?:%s)*)(?P<middle>.*?)(?P<trail>(?:%s)*)$' % \
    ('|'.join([re.escape(x) for x in LEADING_PUNCTUATION]),
    '|'.join([re.escape(x) for x in TRAILING_PUNCTUATION])))
simple_email_re = re.compile(r'^\S+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9._-]+$')
link_target_attribute_re = re.compile(r'(<a [^>]*?)target=[^\s>]+')
html_gunk_re = re.compile(r'(?:<br clear="all">|<i><\/i>|<b><\/b>|<em><\/em>|<strong><\/strong>|<\/?smallcaps>|<\/?uppercase>)', re.IGNORECASE)
hard_coded_bullets_re = re.compile(r'((?:<p>(?:%s).*?[a-zA-Z].*?</p>\s*)+)' % '|'.join([re.escape(x) for x in DOTS]), re.DOTALL)
trailing_empty_content_re = re.compile(r'(?:<p>(?:&nbsp;|\s|<br \/>)*?</p>\s*)+\Z')


# And the template tags themselves...

@register.simple_tag
def optional_login(request):
    """
    Include a login snippet if REST framework's login view is in the URLconf.
    """
    try:
        login_url = reverse('rest_framework:login')
    except NoReverseMatch:
        return ''

    snippet = "<a href='%s?next=%s'>Log in</a>" % (login_url, request.path)
    return snippet


@register.simple_tag
def optional_logout(request):
    """
    Include a logout snippet if REST framework's logout view is in the URLconf.
    """
    try:
        logout_url = reverse('rest_framework:logout')
    except NoReverseMatch:
        return ''

    snippet = "<a href='%s?next=%s'>Log out</a>" % (logout_url, request.path)
    return snippet


@register.simple_tag
def add_query_param(request, key, val):
    """
    Add a query parameter to the current request url, and return the new url.
    """
    return replace_query_param(request.get_full_path(), key, val)


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
def urlize_quoted_links(text, trim_url_limit=None, nofollow=True, autoescape=True):
    """
    Converts any URLs in text into clickable links.

    Works on http://, https://, www. links and links ending in .org, .net or
    .com. Links can have trailing punctuation (periods, commas, close-parens)
    and leading punctuation (opening parens) and it'll still do the right
    thing.

    If trim_url_limit is not None, the URLs in link text longer than this limit
    will truncated to trim_url_limit-3 characters and appended with an elipsis.

    If nofollow is True, the URLs in link text will get a rel="nofollow"
    attribute.

    If autoescape is True, the link text and URLs will get autoescaped.
    """
    trim_url = lambda x, limit=trim_url_limit: limit is not None and (len(x) > limit and ('%s...' % x[:max(0, limit - 3)])) or x
    safe_input = isinstance(text, SafeData)
    words = word_split_re.split(force_text(text))
    nofollow_attr = nofollow and ' rel="nofollow"' or ''
    for i, word in enumerate(words):
        match = None
        if '.' in word or '@' in word or ':' in word:
            match = punctuation_re.match(word)
        if match:
            lead, middle, trail = match.groups()
            # Make URL we want to point to.
            url = None
            if middle.startswith('http://') or middle.startswith('https://'):
                url = middle
            elif middle.startswith('www.') or ('@' not in middle and \
                    middle and middle[0] in string.ascii_letters + string.digits and \
                    (middle.endswith('.org') or middle.endswith('.net') or middle.endswith('.com'))):
                url = 'http://%s' % middle
            elif '@' in middle and not ':' in middle and simple_email_re.match(middle):
                url = 'mailto:%s' % middle
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
    return mark_safe(''.join(words))
