"""
We perform uniqueness checks explicitly on the serializer class, rather
the using Django's `.full_clean()`.

This gives us better separation of concerns, allows us to use single-step
object creation, and makes it possible to switch between using the implicit
`ModelSerializer` class and an equivelent explicit `Serializer` class.
"""
from django.utils.translation import ugettext_lazy as _
from rest_framework.exceptions import ValidationError
from rest_framework.utils.representation import smart_repr


class UniqueValidator:
    """
    Validator that corresponds to `unique=True` on a model field.

    Should be applied to an individual field on the serializer.
    """
    message = _('This field must be unique.')

    def __init__(self, queryset, message=None):
        self.queryset = queryset
        self.serializer_field = None
        self.message = message or self.message

    def set_context(self, serializer_field):
        # Determine the underlying model field name. This may not be the
        # same as the serializer field name if `source=<>` is set.
        self.field_name = serializer_field.source_attrs[0]
        # Determine the existing instance, if this is an update operation.
        self.instance = getattr(serializer_field.parent, 'instance', None)

    def __call__(self, value):
        # Ensure uniqueness.
        filter_kwargs = {self.field_name: value}
        queryset = self.queryset.filter(**filter_kwargs)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)
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

    Should be applied to the serializer class, not to an individual field.
    """
    message = _('The fields {field_names} must make a unique set.')

    def __init__(self, queryset, fields, message=None):
        self.queryset = queryset
        self.fields = fields
        self.serializer_field = None
        self.message = message or self.message

    def set_context(self, serializer):
        # Determine the existing instance, if this is an update operation.
        self.instance = getattr(serializer, 'instance', None)

    def __call__(self, attrs):
        # Ensure uniqueness.
        filter_kwargs = dict([
            (field_name, attrs[field_name]) for field_name in self.fields
        ])
        queryset = self.queryset.filter(**filter_kwargs)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            field_names = ', '.join(self.fields)
            raise ValidationError(self.message.format(field_names=field_names))

    def __repr__(self):
        return '<%s(queryset=%s, fields=%s)>' % (
            self.__class__.__name__,
            smart_repr(self.queryset),
            smart_repr(self.fields)
        )


class BaseUniqueForValidator:
    message = None

    def __init__(self, queryset, field, date_field, message=None):
        self.queryset = queryset
        self.field = field
        self.date_field = date_field
        self.message = message or self.message

    def set_context(self, serializer):
        # Determine the underlying model field names. These may not be the
        # same as the serializer field names if `source=<>` is set.
        self.field_name = serializer.fields[self.field].source_attrs[0]
        self.date_field_name = serializer.fields[self.date_field].source_attrs[0]
        # Determine the existing instance, if this is an update operation.
        self.instance = getattr(serializer, 'instance', None)

    def get_filter_kwargs(self, attrs):
        raise NotImplementedError('`get_filter_kwargs` must be implemented.')

    def __call__(self, attrs):
        filter_kwargs = self.get_filter_kwargs(attrs)

        queryset = self.queryset.filter(**filter_kwargs)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            message = self.message.format(date_field=self.date_field)
            raise ValidationError({self.field: message})

    def __repr__(self):
        return '<%s(queryset=%s, field=%s, date_field=%s)>' % (
            self.__class__.__name__,
            smart_repr(self.queryset),
            smart_repr(self.field),
            smart_repr(self.date_field)
        )


class UniqueForDateValidator(BaseUniqueForValidator):
    message = _('This field must be unique for the "{date_field}" date.')

    def get_filter_kwargs(self, attrs):
        value = attrs[self.field]
        date = attrs[self.date_field]

        filter_kwargs = {}
        filter_kwargs[self.field_name] = value
        filter_kwargs['%s__day' % self.date_field_name] = date.day
        filter_kwargs['%s__month' % self.date_field_name] = date.month
        filter_kwargs['%s__year' % self.date_field_name] = date.year
        return filter_kwargs


class UniqueForMonthValidator(BaseUniqueForValidator):
    message = _('This field must be unique for the "{date_field}" month.')

    def get_filter_kwargs(self, attrs):
        value = attrs[self.field]
        date = attrs[self.date_field]

        filter_kwargs = {}
        filter_kwargs[self.field_name] = value
        filter_kwargs['%s__month' % self.date_field_name] = date.month
        return filter_kwargs


class UniqueForYearValidator(BaseUniqueForValidator):
    message = _('This field must be unique for the "{date_field}" year.')

    def get_filter_kwargs(self, attrs):
        value = attrs[self.field]
        date = attrs[self.date_field]

        filter_kwargs = {}
        filter_kwargs[self.field_name] = value
        filter_kwargs['%s__year' % self.date_field_name] = date.year
        return filter_kwargs
