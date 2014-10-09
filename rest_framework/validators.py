"""
We perform uniqueness checks explicitly on the serializer class, rather
the using Django's `.full_clean()`.

This gives us better separation of concerns, allows us to use single-step
object creation, and makes it possible to switch between using the implicit
`ModelSerializer` class and an equivelent explicit `Serializer` class.
"""
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from rest_framework.utils.representation import smart_repr


class UniqueValidator:
    """
    Validator that corresponds to `unique=True` on a model field.
    """
    # Validators with `requires_context` will have the field instance
    # passed to them when the field is instantiated.
    requires_context = True
    message = _('This field must be unique.')

    def __init__(self, queryset):
        self.queryset = queryset
        self.serializer_field = None

    def __call__(self, value):
        field = self.serializer_field

        # Determine the model field name that the serializer field corresponds to.
        field_name = field.source_attrs[0] if field.source_attrs else field.field_name

        # Determine the existing instance, if this is an update operation.
        instance = getattr(field.parent, 'instance', None)

        # Ensure uniqueness.
        filter_kwargs = {field_name: value}
        queryset = self.queryset.filter(**filter_kwargs)
        if instance:
            queryset = queryset.exclude(pk=instance.pk)
        if queryset.exists():
            raise ValidationError(self.message)

    def __repr__(self):
        return '<%s(queryset=%s)>' % (
            self.__class__.__name__,
            smart_repr(self.queryset)
        )


class UniqueTogetherValidator:
    """
    Validator that corresponds to `unique_together = (...)` on a model class.
    """
    requires_context = True
    message = _('The fields {field_names} must make a unique set.')

    def __init__(self, queryset, fields):
        self.queryset = queryset
        self.fields = fields
        self.serializer_field = None

    def __call__(self, value):
        serializer = self.serializer_field

        # Determine the existing instance, if this is an update operation.
        instance = getattr(serializer, 'instance', None)

        # Ensure uniqueness.
        filter_kwargs = dict([
            (field_name, value[field_name]) for field_name in self.fields
        ])
        queryset = self.queryset.filter(**filter_kwargs)
        if instance:
            queryset = queryset.exclude(pk=instance.pk)
        if queryset.exists():
            field_names = ', '.join(self.fields)
            raise ValidationError(self.message.format(field_names=field_names))

    def __repr__(self):
        return '<%s(queryset=%s, fields=%s)>' % (
            self.__class__.__name__,
            smart_repr(self.queryset),
            smart_repr(self.fields)
        )
