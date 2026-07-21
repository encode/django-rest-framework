from jinja2.ext import Extension
from rest_framework.renderers import HTMLFormRenderer


class DRFExtension(Extension):
    """Jinja2 extension exposing DRF template rendering functions."""

    def __init__(self, environment):
        super().__init__(environment)
        environment.globals["render_form"] = self.render_form
        environment.globals["render_field"] = self.render_field

    def render_form(self, serializer, style=None):
        """Render a complete HTML form for the given serializer."""
        renderer = HTMLFormRenderer()
        return renderer.render(
            serializer.data,
            renderer_context={"serializer": serializer, "style": style or {}},
        )

    def render_field(self, field, style=None):
        """Render an individual HTML field."""
        renderer = HTMLFormRenderer()
        return renderer.render_field(field, style or {})