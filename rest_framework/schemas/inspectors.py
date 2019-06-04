"""
inspectors.py   # Per-endpoint view introspection

See schemas.__init__.py for package overview.
"""
from weakref import WeakKeyDictionary

from rest_framework.settings import api_settings


class ViewInspector:
    """
    Descriptor class on APIView.

    Provide subclass for per-view schema generation
    """

    def __init__(self):
        self.instance_schemas = WeakKeyDictionary()

    def __get__(self, instance, owner):
        """
        Enables `ViewInspector` as a Python _Descriptor_.

        This is how `view.schema` knows about `view`.

        `__get__` is called when the descriptor is accessed on the owner.
        (That will be when view.schema is called in our case.)

        `owner` is always the owner class. (An APIView, or subclass for us.)
        `instance` is the view instance or `None` if accessed from the class,
        rather than an instance.

        See: https://docs.python.org/3/howto/descriptor.html for info on
        descriptor usage.
        """
        if instance in self.instance_schemas:
            return self.instance_schemas[instance]

        self.view = instance
        return self

    def __set__(self, instance, other):
        self.instance_schemas[instance] = other
        if other is not None:
            other.view = instance

    @property
    def view(self):
        """View property."""
        assert self._view is not None, (
            "Schema generation REQUIRES a view instance. (Hint: you accessed "
            "`schema` from the view class rather than an instance.)"
        )
        return self._view

    @view.setter
    def view(self, value):
        self._view = value

    @view.deleter
    def view(self):
        self._view = None


class DefaultSchema(ViewInspector):
    """Allows overriding AutoSchema using DEFAULT_SCHEMA_CLASS setting"""
    def __get__(self, instance, owner):
        result = super().__get__(instance, owner)
        if not isinstance(result, DefaultSchema):
            return result

        inspector_class = api_settings.DEFAULT_SCHEMA_CLASS
        assert issubclass(inspector_class, ViewInspector), (
            "DEFAULT_SCHEMA_CLASS must be set to a ViewInspector (usually an AutoSchema) subclass"
        )
        inspector = inspector_class()
        inspector.view = instance
        return inspector
