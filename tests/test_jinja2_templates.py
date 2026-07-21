from jinja2 import Environment
from rest_framework import serializers
from rest_framework.jinja2 import DRFExtension


class AddressSerializer(serializers.Serializer):
    street = serializers.CharField()
    city = serializers.CharField()


class UserSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=50)
    email = serializers.EmailField()
    age = serializers.IntegerField(min_value=0)
    address = AddressSerializer()


def test_render_form_basic():
    env = Environment(extensions=[DRFExtension])
    template = env.from_string("{{ render_form(serializer) }}")

    data = {
        "username": "alice",
        "email": "alice@example.com",
        "age": 30,
        "address": {"street": "123 Main St", "city": "Springfield"},
    }
    serializer = UserSerializer(data=data)
    serializer.is_valid()

    html = template.render(serializer=serializer)
    assert "alice" in html
    assert "alice@example.com" in html


def test_render_form_with_validation_errors():
    env = Environment(extensions=[DRFExtension])
    template = env.from_string("{{ render_form(serializer) }}")

    serializer = UserSerializer(data={"username": "", "email": "invalid-email"})
    serializer.is_valid()

    html = template.render(serializer=serializer)
    assert "error" in html.lower() or "invalid" in html.lower()


def test_render_field_individual():
    env = Environment(extensions=[DRFExtension])
    template = env.from_string("{{ render_field(serializer.username) }}")

    data = {
        "username": "bob",
        "email": "bob@example.com",
        "age": 25,
        "address": {"street": "456 Elm", "city": "Shelbyville"},
    }
    serializer = UserSerializer(data=data)
    serializer.is_valid()

    html = template.render(serializer=serializer)
    assert "bob" in html


def test_render_field_with_custom_style():
    env = Environment(extensions=[DRFExtension])
    template = env.from_string(
        "{{ render_field(serializer.email, style={'base_template': 'textarea.html'}) }}"
    )

    data = {
        "username": "charlie",
        "email": "charlie@example.com",
        "age": 40,
        "address": {"street": "789 Oak", "city": "Capital City"},
    }
    serializer = UserSerializer(data=data)
    serializer.is_valid()

    html = template.render(serializer=serializer)
    assert "charlie@example.com" in html