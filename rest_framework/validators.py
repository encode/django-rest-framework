from django.core.exceptions import ValidationError


class UniqueValidator:
    # Validators with `requires_context` will have the field instance
    # passed to them when the field is instantiated.
    requires_context = True

    def __init__(self, queryset):
        self.queryset = queryset
        self.serializer_field = None

    def get_queryset(self):
        return self.queryset.all()

    def __call__(self, value):
        field = self.serializer_field

        # Determine the model field name that the serializer field corresponds to.
        field_name = field.source_attrs[0] if field.source_attrs else field.field_name

        # Determine the existing instance, if this is an update operation.
        instance = getattr(field.parent, 'instance', None)

        # Ensure uniqueness.
        filter_kwargs = {field_name: value}
        queryset = self.get_queryset().filter(**filter_kwargs)
        if instance:
            queryset = queryset.exclude(pk=instance.pk)
        if queryset.exists():
            raise ValidationError('This field must be unique.')


class UniqueTogetherValidator:
    requires_context = True

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
        queryset = self.get_queryset().filter(**filter_kwargs)
        if instance:
            queryset = queryset.exclude(pk=instance.pk)
        if queryset.exists():
            field_names = ' and '.join(self.fields)
            raise ValidationError('The fields %s must make a unique set.' % field_names)
