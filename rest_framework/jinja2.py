from jinja2.ext import Extension
from markupsafe import Markup

from rest_framework.renderers import HTMLFormRenderer


class DRFExtension(Extension):
    """Jinja2 extension exposing DRF template rendering functions."""

    def __init__(self, environment):
        super().__init__(environment)
        environment.globals["render_form"] = self.render_form
        environment.globals["render_field"] = self.render_field

    def render_form(self, serializer, template_pack=None):
        """Render a complete HTML form for the given serializer."""
        style = {"template_pack": template_pack} if template_pack else {}
        renderer = HTMLFormRenderer()
        return Markup(renderer.render(serializer.data, None, {"style": style}))

    def render_field(self, field, style=None):
        """Render an individual HTML field."""
        renderer = (
            style.get("renderer", HTMLFormRenderer()) if style else HTMLFormRenderer()
        )
        html = renderer.render_field(field, style or {})
        return Markup(html)
