import re
from django import template
from django.template import loader
from django.urls import NoReverseMatch, reverse
from django.utils.encoding import iri_to_uri
from django.utils.html import escape, format_html, smart_urlquote
from django.utils.safestring import mark_safe

from rest_framework.compat import apply_markdown, pygments_highlight
from rest_framework.renderers import HTMLFormRenderer
from rest_framework.utils.urls import replace_query_param

register = template.Library()

# Precompile regex patterns
class_re = re.compile(r'(?<=class=["\'])(.*?)(?=["\'])')

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
    return [field for field in fields if field.location == location]

@register.simple_tag
def form_for_link(link):
    import coreschema
    properties = {field.name: field.schema or coreschema.String() for field in link.fields}
    required = [field.name for field in link.fields if field.required]
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
def optional_logout(request, user, csrf_token):
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
            <form id="logoutForm" method="post" action="{href}?next={next}">
                <input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">
            </form>
            <li>
                <a href="#" onclick='document.getElementById("logoutForm").submit()'>Log out</a>
            </li>
        </ul>
    </li>"""
    snippet = format_html(snippet, user=escape(user), href=logout_url, next=escape(request.path), csrf_token=csrf_token)
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
    return '' if value is None else '%s' % value

@register.filter
def as_list_of_strings(value):
    return ['' if item is None else '%s' % item for item in value]

@register.filter
def add_class(value, css_class):
    html = str(value)
    match = class_re.search(html)
    if match:
        classes = match.group(1)
        if css_class not in classes.split():
            classes += f" {css_class}"
            html = class_re.sub(classes, html)
    else:
        html = html.replace('>', f' class="{css_class}">', 1)
    return mark_safe(html)

@register.filter
def format_value(value):
    if getattr(value, 'is_hyperlink', False):
        name = str(value.obj)
        return mark_safe(f'<a href={value}>{escape(name)}</a>')
    if value is None or isinstance(value, bool):
        return mark_safe(f'<code>{value}</code>')
    if isinstance(value, list):
        if any(isinstance(item, (list, dict)) for item in value):
            template = loader.get_template('rest_framework/admin/list_value.html')
        else:
            template = loader.get_template('rest_framework/admin/simple_list_value.html')
        return template.render({'value': value})
    if isinstance(value, dict):
        template = loader.get_template('rest_framework/admin/dict_value.html')
        return template.render({'value': value})
    if isinstance(value, str):
        if (value.startswith('http') or value.startswith('/')) and not re.search(r'\s', value):
            return mark_safe(f'<a href="{escape(value)}">{escape(value)}</a>')
        if '@' in value and not re.search(r'\s', value):
            return mark_safe(f'<a href="mailto:{escape(value)}">{escape(value)}</a>')
        if '\n' in value:
            return mark_safe(f'<pre>{escape(value)}</pre>')
    return str(value)

@register.filter
def items(value):
    return [] if value is None else value.items()

@register.filter
def data(value):
    return value.data

@register.filter
def schema_links(section, sec_key=None):
    """
    Recursively find every link in a schema, even nested.
    """
    NESTED_FORMAT = '%s > %s'
    links = section.links
    if section.data:
        data = section.data.items()
        for sub_section_key, sub_section in data:
            new_links = schema_links(sub_section, sec_key=sub_section_key)
            links.update(new_links)
    if sec_key is not None:
        new_links = {NESTED_FORMAT % (sec_key, link_key): link for link_key, link in links.items()}
        return new_links
    return links

@register.filter
def add_nested_class(value):
    if isinstance(value, dict) or (isinstance(value, list) and any(isinstance(item, (list, dict)) for item in value)):
        return 'class=nested'
    return ''

TRAILING_PUNCTUATION = ['.', ',', ':', ';', '.)', '"', "']", "'}"]
WRAPPING_PUNCTUATION = [('(', ')'), ('<', '>'), ('[', ']'), ('&lt;', '&gt;'), ('"', '"'), ("'", "'")]
word_split_re = re.compile(r'(\s+)')
simple_url_re = re.compile(r'^https?://\[?\w', re.IGNORECASE)
simple_url_2_re = re.compile(r'^www\.|^(?!http)\w[^@]+\.(com|edu|gov|int|mil|net|org)$', re.IGNORECASE)
simple_email_re = re.compile(r'^\S+@\S+\.\S+$')

def smart_urlquote_wrapper(matched_url):
    try:
        return smart_urlquote(matched_url)
    except ValueError:
        return None

@register.filter
def break_long_headers(header):
    if len(header) > 160 and ',' in header:
        header = mark_safe('<br> ' + ', <br>'.join(escape(header).split(',')))
    return header
