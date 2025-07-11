from coreschema import Object, Array, String, Integer, Number, Boolean, Enum
import jinja2


env = jinja2.Environment(loader=jinja2.PackageLoader('coreschema', 'templates'))


# TODO: required
# TODO: initial values, errors, input control


def render_to_form(schema):
    template = env.get_template('form.html')
    return template.render({
        'parent': schema,
        'determine_html_template': determine_html_template,
        'get_textarea_value': get_textarea_value,
        'get_attrs': get_attrs
    })


def determine_html_template(schema):
    if isinstance(schema, Array):
        if schema.unique_items and isinstance(schema.items, Enum):
            # Actually only for *unordered* input
            return 'bootstrap3/inputs/select_multiple.html'
        # TODO: Comma seperated inputs
        return 'bootstrap3/inputs/textarea.html'
    elif isinstance(schema, Object):
        # TODO: Fieldsets
        return 'bootstrap3/inputs/textarea.html'
    elif isinstance(schema, Number):
        return 'bootstrap3/inputs/input.html'
    elif isinstance(schema, Boolean):
        # TODO: nullable boolean
        return 'bootstrap3/inputs/checkbox.html'
    elif isinstance(schema, Enum):
        # TODO: display values
        return 'bootstrap3/inputs/select.html'
    # String:
    if schema.format == 'textarea':
        return 'bootstrap3/inputs/textarea.html'
    return 'bootstrap3/inputs/input.html'


def get_textarea_value(schema):
    if isinstance(schema, Array):
        return "[ ]"
    elif isinstance(schema, Object):
        return "{ }"
    return ""


def get_attrs(schema):
    if isinstance(schema, Array):
        # TODO: Add data-child-type and use with selects
        return "data-empty=[] data-type='array'"
    elif isinstance(schema, Object):
        return "data-empty={} data-type='object'"
    elif isinstance(schema, Integer):
        return "data-empty=null data-type='integer' type='number' step=1"
    elif isinstance(schema, Number):
        return "data-empty=null data-type='number' type='number' step=any"
    elif isinstance(schema, Boolean):
        return "data-empty=false data-type='boolean'"
    elif isinstance(schema, Enum):
        # TODO: Non-string Enum
        return "data-empty='' data-type='string'"
    # String:
    if schema.format:
        # TODO: Only include valid HTML5 formats.
        #       Coerce datetime to datetime-local.
        return "data-empty='' data-type='string' type='%s'" % schema.format
    return "data-empty='' data-type='string'"
