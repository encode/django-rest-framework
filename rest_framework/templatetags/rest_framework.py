from __future__ import unicode_literals, absolute_import
from django import template
from django.core.urlresolvers import reverse, NoReverseMatch
from django.http import QueryDict
from django.utils.encoding import iri_to_uri
from django.utils.html import escape
from django.utils.safestring import SafeData, mark_safe
from rest_framework.compat import urlparse, force_text, six, smart_urlquote
import re

register = template.Library()


# Note we don't use 'load staticfiles', because we need a 1.3 compatible
# version, so instead we include the `static` template tag ourselves.

# When 1.3 becomes unsupported by REST framework, we can instead start to
# use the {% load staticfiles %} tag, remove the following code,
# and add a dependency that `django.contrib.staticfiles` must be installed.

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

    snippet = "<a href='%s?next=%s'>Log in</a>" % (login_url, escape(request.path))
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

    snippet = "<a href='%s?next=%s'>Log out</a>" % (logout_url, escape(request.path))
    return snippet


@register.simple_tag
def add_query_param(request, key, val):
    """
    Add a query parameter to the current request url, and return the new url.
    """
    iri = request.get_full_path()
    uri = iri_to_uri(iri)
    return replace_query_param(uri, key, val)


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
    trim_url = lambda x, limit=trim_url_limit: limit is not None and (len(x) > limit and ('%s...' % x[:max(0, limit - 3)])) or x
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
                if (middle.endswith(closing)
                    and middle.count(closing) == middle.count(opening) + 1):
                    middle = middle[:-len(closing)]
                    trail = closing + trail

            # Make URL we want to point to.
            url = None
            nofollow_attr = ' rel="nofollow"' if nofollow else ''
            if simple_url_re.match(middle):
                url = smart_urlquote_wrapper(middle)
            elif simple_url_2_re.match(middle):
                url = smart_urlquote_wrapper('http://%s' % middle)
            elif not ':' in middle and simple_email_re.match(middle):
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
