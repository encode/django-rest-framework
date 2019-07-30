import re
from collections import OrderedDict

from django import template
from django.template import loader
from django.urls import NoReverseMatch, reverse
from django.utils.encoding import force_str, iri_to_uri
from django.utils.html import escape, format_html, smart_urlquote
from django.utils.safestring import SafeData, mark_safe

from rest_framework.compat import apply_markdown, pygments_highlight
from rest_framework.renderers import HTMLFormRenderer
from rest_framework.utils.urls import replace_query_param

register = template.Library()

# Regex for adding classes to html snippets
class_re = re.compile(r'(?<=class=["\'])(.*)(?=["\'])')


@register.tag(name='code')
def highlight_code(parser, token):
    code = token.split_contents()[-1]
    nodelist = parser.parse(('endcode',))
    parser.delete_first_token()
    return CodeNode(code, nodelist)


class CodeNode(template.Node):
    style = 'emacs'

    def __init__(self, lang, code):
        self.lang = lang
        self.nodelist = code

    def render(self, context):
        text = self.nodelist.render(context)
        return pygments_highlight(text, self.lang, self.style)


@register.filter()
def with_location(fields, location):
    return [
        field for field in fields
        if field.location == location
    ]


@register.simple_tag
def form_for_link(link):
    import coreschema
    properties = OrderedDict([
        (field.name, field.schema or coreschema.String())
        for field in link.fields
    ])
    required = [
        field.name
        for field in link.fields
        if field.required
    ]
    schema = coreschema.Object(properties=properties, required=required)
    return mark_safe(coreschema.render_to_form(schema))


@register.simple_tag
def render_markdown(markdown_text):
    if apply_markdown is None:
        return markdown_text
    return mark_safe(apply_markdown(markdown_text))


@register.simple_tag
def get_pagination_html(pager):
    return pager.to_html()


@register.simple_tag
def render_form(serializer, template_pack=None):
    style = {'template_pack': template_pack} if template_pack else {}
    renderer = HTMLFormRenderer()
    return renderer.render(serializer.data, None, {'style': style})


@register.simple_tag
def render_field(field, style):
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
    snippet = format_html(snippet, href=login_url, next=escape(request.path))

    return mark_safe(snippet)


@register.simple_tag
def optional_docs_login(request):
    """
    Include a login snippet if REST framework's login view is in the URLconf.
    """
    try:
        login_url = reverse('rest_framework:login')
    except NoReverseMatch:
        return 'log in'

    snippet = "<a href='{href}?next={next}'>log in</a>"
    snippet = format_html(snippet, href=login_url, next=escape(request.path))

    return mark_safe(snippet)


@register.simple_tag
def optional_logout(request, user):
    """
    Include a logout snippet if REST framework's logout view is in the URLconf.
    """
    try:
        logout_url = reverse('rest_framework:logout')
    except NoReverseMatch:
        snippet = format_html('<li class="navbar-text">{user}</li>', user=escape(user))
        return mark_safe(snippet)

    snippet = """<li class="dropdown">
        <a href="#" class="dropdown-toggle" data-toggle="dropdown">
            {user}
            <b class="caret"></b>
        </a>
        <ul class="dropdown-menu">
            <li><a href='{href}?next={next}'>Log out</a></li>
        </ul>
    </li>"""
    snippet = format_html(snippet, user=escape(user), href=logout_url, next=escape(request.path))

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
def as_string(value):
    if value is None:
        return ''
    return '%s' % value


@register.filter
def as_list_of_strings(value):
    return [
        '' if (item is None) else ('%s' % item)
        for item in value
    ]


@register.filter
def add_class(value, css_class):
    """
    https://stackoverflow.com/questions/4124220/django-adding-css-classes-when-rendering-form-fields-in-a-template

    Inserts classes into template variables that contain HTML tags,
    useful for modifying forms without needing to change the Form objects.

    Usage:

        {{ field.label_tag|add_class:"control-label" }}

    In the case of REST Framework, the filter is used to add Bootstrap-specific
    classes to the forms.
    """
    html = str(value)
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
        name = str(value.obj)
        return mark_safe('<a href=%s>%s</a>' % (value, escape(name)))
    if value is None or isinstance(value, bool):
        return mark_safe('<code>%s</code>' % {True: 'true', False: 'false', None: 'null'}[value])
    elif isinstance(value, list):
        if any([isinstance(item, (list, dict)) for item in value]):
            template = loader.get_template('rest_framework/admin/list_value.html')
        else:
            template = loader.get_template('rest_framework/admin/simple_list_value.html')
        context = {'value': value}
        return template.render(context)
    elif isinstance(value, dict):
        template = loader.get_template('rest_framework/admin/dict_value.html')
        context = {'value': value}
        return template.render(context)
    elif isinstance(value, str):
        if (
            (value.startswith('http:') or value.startswith('https:')) and not
            re.search(r'\s', value)
        ):
            return mark_safe('<a href="{value}">{value}</a>'.format(value=escape(value)))
        elif '@' in value and not re.search(r'\s', value):
            return mark_safe('<a href="mailto:{value}">{value}</a>'.format(value=escape(value)))
        elif '\n' in value:
            return mark_safe('<pre>%s</pre>' % escape(value))
    return str(value)


@register.filter
def items(value):
    """
    Simple filter to return the items of the dict. Useful when the dict may
    have a key 'items' which is resolved first in Django template dot-notation
    lookup.  See issue #4931
    Also see: https://stackoverflow.com/questions/15416662/django-template-loop-over-dictionary-items-with-items-as-key
    """
    if value is None:
        # `{% for k, v in value.items %}` doesn't raise when value is None or
        # not in the context, so neither should `{% for k, v in value|items %}`
        return []
    return value.items()


@register.filter
def data(value):
    """
    Simple filter to access `data` attribute of object,
    specifically coreapi.Document.

    As per `items` filter above, allows accessing `document.data` when
    Document contains Link keyed-at "data".

    See issue #5395
    """
    return value.data


@register.filter
def schema_links(section, sec_key=None):
    """
    Recursively find every link in a schema, even nested.
    """
    NESTED_FORMAT = '%s > %s'  # this format is used in docs/js/api.js:normalizeKeys
    links = section.links
    if section.data:
        data = section.data.items()
        for sub_section_key, sub_section in data:
            new_links = schema_links(sub_section, sec_key=sub_section_key)
            links.update(new_links)

    if sec_key is not None:
        new_links = OrderedDict()
        for link_key, link in links.items():
            new_key = NESTED_FORMAT % (sec_key, link_key)
            new_links.update({new_key: link})
        return new_links

    return links


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


@register.filter(needs_autoescape=True)
def urlize_quoted_links(text, trim_url_limit=None, nofollow=True, autoescape=True):
    """
    Converts any URLs in text into clickable links.

    Works on http://, https://, www. links, and also on links ending in one of
    the original seven gTLDs (.com, .edu, .gov, .int, .mil, .net, and .org).
    Links can have trailing punctuation (periods, commas, close-parens) and
    leading punctuation (opening parens) and it'll still do the right thing.

    If trim_url_limit is not None, the URLs in link text longer than this limit
    will truncated to trim_url_limit-3 characters and appended with an ellipsis.

    If nofollow is True, the URLs in link text will get a rel="nofollow"
    attribute.

    If autoescape is True, the link text and URLs will get autoescaped.
    """
    def trim_url(x, limit=trim_url_limit):
        return limit is not None and (len(x) > limit and ('%s...' % x[:max(0, limit - 3)])) or x

    safe_input = isinstance(text, SafeData)

    # Unfortunately, Django built-in cannot be used here, because escaping
    # is to be performed on words, which have been forcibly coerced to text
    def conditional_escape(text):
        return escape(text) if autoescape and not safe_input else text

    words = word_split_re.split(force_str(text))
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
                lead, trail = conditional_escape(lead), conditional_escape(trail)
                url, trimmed = conditional_escape(url), conditional_escape(trimmed)
                middle = '<a href="%s"%s>%s</a>' % (url, nofollow_attr, trimmed)
                words[i] = '%s%s%s' % (lead, middle, trail)
            else:
                words[i] = conditional_escape(word)
        else:
            words[i] = conditional_escape(word)
    return mark_safe(''.join(words))


@register.filter
def break_long_headers(header):
    """
    Breaks headers longer than 160 characters (~page length)
    when possible (are comma separated)
    """
    if len(header) > 160 and ',' in header:
        header = mark_safe('<br> ' + ', <br>'.join(header.split(',')))
    return header
