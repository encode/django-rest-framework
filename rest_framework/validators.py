"""
We perform uniqueness checks explicitly on the serializer class, rather
the using Django's `.full_clean()`.

This gives us better separation of concerns, allows us to use single-step
object creation, and makes it possible to switch between using the implicit
`ModelSerializer` class and an equivalent explicit `Serializer` class.
"""
from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _
from rest_framework.compat import unicode_to_repr
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
        """
        This hook is called by the serializer instance,
        prior to the validation call being made.
        """
        # Determine the underlying model field name. This may not be the
        # same as the serializer field name if `source=<>` is set.
        self.field_name = serializer_field.source_attrs[0]
        # Determine the existing instance, if this is an update operation.
        self.instance = getattr(serializer_field.parent, 'instance', None)

    def filter_queryset(self, value, queryset):
        """
        Filter the queryset to all instances matching the given attribute.
        """
        filter_kwargs = {self.field_name: value}
        return queryset.filter(**filter_kwargs)

    def exclude_current_instance(self, queryset):
        """
        If an instance is being updated, then do not include
        that instance itself as a uniqueness conflict.
        """
        if self.instance is not None:
            return queryset.exclude(pk=self.instance.pk)
        return queryset

    def __call__(self, value):
        queryset = self.queryset
        queryset = self.filter_queryset(value, queryset)
        queryset = self.exclude_current_instance(queryset)
        if queryset.exists():
            raise ValidationError(self.message)

    def __repr__(self):
        return unicode_to_repr('<%s(queryset=%s)>' % (
            self.__class__.__name__,
            smart_repr(self.queryset)
        ))


class UniqueTogetherValidator:
    """
    Validator that corresponds to `unique_together = (...)` on a model class.

    Should be applied to the serializer class, not to an individual field.
    """
    message = _('The fields {field_names} must make a unique set.')
    missing_message = _('This field is required.')

    def __init__(self, queryset, fields, message=None):
        self.queryset = queryset
        self.fields = fields
        self.serializer_field = None
        self.message = message or self.message

    def set_context(self, serializer):
        """
        This hook is called by the serializer instance,
        prior to the validation call being made.
        """
        # Determine the existing instance, if this is an update operation.
        self.instance = getattr(serializer, 'instance', None)

    def enforce_required_fields(self, attrs):
        """
        The `UniqueTogetherValidator` always forces an implied 'required'
        state on the fields it applies to.
        """
        if self.instance is not None:
            return

        missing = dict([
            (field_name, self.missing_message)
            for field_name in self.fields
            if field_name not in attrs
        ])
        if missing:
            raise ValidationError(missing)

    def filter_queryset(self, attrs, queryset):
        """
        Filter the queryset to all instances matching the given attributes.
        """
        # If this is an update, then any unprovided field should
        # have it's value set based on the existing instance attribute.
        if self.instance is not None:
            for field_name in self.fields:
                if field_name not in attrs:
                    attrs[field_name] = getattr(self.instance, field_name)

        # Determine the filter keyword arguments and filter the queryset.
        filter_kwargs = dict([
            (field_name, attrs[field_name])
            for field_name in self.fields
        ])
        return queryset.filter(**filter_kwargs)

    def exclude_current_instance(self, attrs, queryset):
        """
        If an instance is being updated, then do not include
        that instance itself as a uniqueness conflict.
        """
        if self.instance is not None:
            return queryset.exclude(pk=self.instance.pk)
        return queryset

    def __call__(self, attrs):
        self.enforce_required_fields(attrs)
        queryset = self.queryset
        queryset = self.filter_queryset(attrs, queryset)
        queryset = self.exclude_current_instance(attrs, queryset)
        if queryset.exists():
            field_names = ', '.join(self.fields)
            raise ValidationError(self.message.format(field_names=field_names))

    def __repr__(self):
        return unicode_to_repr('<%s(queryset=%s, fields=%s)>' % (
            self.__class__.__name__,
            smart_repr(self.queryset),
            smart_repr(self.fields)
        ))


class BaseUniqueForValidator:
    message = None
    missing_message = _('This field is required.')

    def __init__(self, queryset, field, date_field, message=None):
        self.queryset = queryset
        self.field = field
        self.date_field = date_field
        self.message = message or self.message

    def set_context(self, serializer):
        """
        This hook is called by the serializer instance,
        prior to the validation call being made.
        """
        # Determine the underlying model field names. These may not be the
        # same as the serializer field names if `source=<>` is set.
        self.field_name = serializer.fields[self.field].source_attrs[0]
        self.date_field_name = serializer.fields[self.date_field].source_attrs[0]
        # Determine the existing instance, if this is an update operation.
        self.instance = getattr(serializer, 'instance', None)

    def enforce_required_fields(self, attrs):
        """
        The `UniqueFor<Range>Validator` classes always force an implied
        'required' state on the fields they are applied to.
        """
        missing = dict([
            (field_name, self.missing_message)
            for field_name in [self.field, self.date_field]
            if field_name not in attrs
        ])
        if missing:
            raise ValidationError(missing)

    def filter_queryset(self, attrs, queryset):
        raise NotImplementedError('`filter_queryset` must be implemented.')

    def exclude_current_instance(self, attrs, queryset):
        """
        If an instance is being updated, then do not include
        that instance itself as a uniqueness conflict.
        """
        if self.instance is not None:
            return queryset.exclude(pk=self.instance.pk)
        return queryset

    def __call__(self, attrs):
        self.enforce_required_fields(attrs)
        queryset = self.queryset
        queryset = self.filter_queryset(attrs, queryset)
        queryset = self.exclude_current_instance(attrs, queryset)
        if queryset.exists():
            message = self.message.format(date_field=self.date_field)
            raise ValidationError({self.field: message})

    def __repr__(self):
        return unicode_to_repr('<%s(queryset=%s, field=%s, date_field=%s)>' % (
            self.__class__.__name__,
            smart_repr(self.queryset),
            smart_repr(self.field),
            smart_repr(self.date_field)
        ))


class UniqueForDateValidator(BaseUniqueForValidator):
    message = _('This field must be unique for the "{date_field}" date.')

    def filter_queryset(self, attrs, queryset):
        value = attrs[self.field]
        date = attrs[self.date_field]

        filter_kwargs = {}
        filter_kwargs[self.field_name] = value
        filter_kwargs['%s__day' % self.date_field_name] = date.day
        filter_kwargs['%s__month' % self.date_field_name] = date.month
        filter_kwargs['%s__year' % self.date_field_name] = date.year
        return queryset.filter(**filter_kwargs)


class UniqueForMonthValidator(BaseUniqueForValidator):
    message = _('This field must be unique for the "{date_field}" month.')

    def filter_queryset(self, attrs, queryset):
        value = attrs[self.field]
        date = attrs[self.date_field]

        filter_kwargs = {}
        filter_kwargs[self.field_name] = value
        filter_kwargs['%s__month' % self.date_field_name] = date.month
        return queryset.filter(**filter_kwargs)


class UniqueForYearValidator(BaseUniqueForValidator):
    message = _('This field must be unique for the "{date_field}" year.')

    def filter_queryset(self, attrs, queryset):
        value = attrs[self.field]
        date = attrs[self.date_field]

        filter_kwargs = {}
        filter_kwargs[self.field_name] = value
        filter_kwargs['%s__year' % self.date_field_name] = date.year
        return queryset.filter(**filter_kwargs)
