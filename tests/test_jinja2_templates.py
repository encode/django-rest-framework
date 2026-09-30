import importlib

import pytest

from rest_framework import serializers


def load_jinja():
    pytest.importorskip("jinja2")
    jinja2 = importlib.import_module("jinja2")
    DRFExtension = importlib.import_module("rest_framework.jinja2").DRFExtension
    return jinja2.Environment, DRFExtension


class SimpleSerializer(serializers.Serializer):
    name = serializers.CharField()
    age = serializers.IntegerField()


def test_jinja2_render_form_with_extension():
    """
    Test that the DRF Jinja2 extension correctly exposes render_form
    and render_field to the Jinja2 environment.
    """
    Environment, DRFExtension = load_jinja()

    # Setup Jinja2 environment with the new DRF extension
    env = Environment(extensions=[DRFExtension])

    # Create a template that uses the DRF rendering functions
    template_str = """
    {% set form_data = render_form(serializer) %}
    {{ form_data }}
    """
    template = env.from_string(template_str)

    serializer = SimpleSerializer(data={"name": "Mohammed", "age": 30})
    serializer.is_valid()

    # Render the template
    output = template.render(serializer=serializer)

    # Assertions: Verify the output contains expected HTML form elements
    assert (
        "<form" in output or "name" in output.lower()
    ), "Expected form rendering to contain field data"
    assert "Mohammed" in output, "Expected rendered form to contain the serializer data"


def test_jinja2_render_field_individual():
    """
    Test that render_field works individually in Jinja2.
    """
    Environment, DRFExtension = load_jinja()
    env = Environment(extensions=[DRFExtension])
    template_str = "{{ render_field(serializer['name']) }}"
    template = env.from_string(template_str)

    serializer = SimpleSerializer(data={"name": "Ahmed", "age": 25})
    serializer.is_valid()

    output = template.render(serializer=serializer)

    assert (
        "Ahmed" in output or "name" in output.lower()
    ), "Expected field rendering to work"


def test_jinja2_render_form_with_template_pack():
    """
    Test that render_form mirrors the template-tag API in Jinja2.
    """
    Environment, DRFExtension = load_jinja()
    env = Environment(extensions=[DRFExtension])
    template = env.from_string(
        '{{ render_form(serializer, template_pack="rest_framework/vertical") }}'
    )

    serializer = SimpleSerializer(data={"name": "Ali", "age": 41})
    serializer.is_valid()

    output = template.render(serializer=serializer)

    assert "Ali" in output, "Expected rendered form to contain serializer data"


def test_jinja2_render_field_with_style():
    """
    Test that render_field accepts the same style mapping the template tag does.
    """
    Environment, DRFExtension = load_jinja()
    env = Environment(extensions=[DRFExtension])
    template = env.from_string(
        "{{ render_field(serializer['name'], style={'base_template': 'textarea.html'}) }}"
    )

    serializer = SimpleSerializer(data={"name": "Asiya", "age": 23})
    serializer.is_valid()

    output = template.render(serializer=serializer)

    assert "Asiya" in output, "Expected rendered field to contain serializer data"


def test_jinja2_render_form_with_autoescape_preserves_html():
    """
    Test that extension output is marked safe so autoescaped environments keep HTML intact.
    """
    Environment, DRFExtension = load_jinja()
    env = Environment(autoescape=True, extensions=[DRFExtension])
    template = env.from_string("{{ render_form(serializer) }}")

    serializer = SimpleSerializer(data={"name": "Hajar", "age": 28})
    serializer.is_valid()

    output = template.render(serializer=serializer)

    assert (
        '<div class="form-group' in output
    ), "Expected rendered form HTML to remain unescaped"
    assert "Hajar" in output, "Expected rendered form to contain serializer data"
