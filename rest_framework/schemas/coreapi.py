from collections import Counter

from django.db import models
from django.utils.encoding import force_str

from rest_framework import serializers
from rest_framework.compat import coreschema


def common_path(paths):
    split_paths = [path.strip('/').split('/') for path in paths]
    s1 = min(split_paths)
    s2 = max(split_paths)
    common = s1
    for i, c in enumerate(s1):
        if c != s2[i]:
            common = s1[:i]
            break
    return '/' + '/'.join(common)


def is_custom_action(action):
    return action not in {
        'retrieve', 'list', 'create', 'update', 'partial_update', 'destroy'
    }


def distribute_links(obj):
    for key, value in obj.items():
        distribute_links(value)

    for preferred_key, link in obj.links:
        key = obj.get_available_key(preferred_key)
        obj[key] = link


INSERT_INTO_COLLISION_FMT = """
Schema Naming Collision.

coreapi.Link for URL path {value_url} cannot be inserted into schema.
Position conflicts with coreapi.Link for URL path {target_url}.

Attempted to insert link with keys: {keys}.

Adjust URLs to avoid naming collision or override `SchemaGenerator.get_keys()`
to customise schema structure.
"""


class LinkNode(dict):
    def __init__(self):
        self.links = []
        self.methods_counter = Counter()
        super().__init__()

    def get_available_key(self, preferred_key):
        if preferred_key not in self:
            return preferred_key

        while True:
            current_val = self.methods_counter[preferred_key]
            self.methods_counter[preferred_key] += 1

            key = f'{preferred_key}_{current_val}'
            if key not in self:
                return key


def insert_into(target, keys, value):
    """
    Nested dictionary insertion.

    >>> example = {}
    >>> insert_into(example, ['a', 'b', 'c'], 123)
    >>> example
    LinkNode({'a': LinkNode({'b': LinkNode({'c': LinkNode(links=[123])}}})))
    """
    for key in keys[:-1]:
        if key not in target:
            target[key] = LinkNode()
        target = target[key]

    try:
        target.links.append((keys[-1], value))
    except TypeError:
        msg = INSERT_INTO_COLLISION_FMT.format(
            value_url=value.url,
            target_url=target.url,
            keys=keys
        )
        raise ValueError(msg)


# View Inspectors #


def field_to_schema(field):
    title = force_str(field.label) if field.label else ''
    description = force_str(field.help_text) if field.help_text else ''

    if isinstance(field, (serializers.ListSerializer, serializers.ListField)):
        child_schema = field_to_schema(field.child)
        return coreschema.Array(
            items=child_schema,
            title=title,
            description=description
        )
    elif isinstance(field, serializers.DictField):
        return coreschema.Object(
            title=title,
            description=description
        )
    elif isinstance(field, serializers.Serializer):
        return coreschema.Object(
            properties={
                key: field_to_schema(value)
                for key, value
                in field.fields.items()
            },
            title=title,
            description=description
        )
    elif isinstance(field, serializers.ManyRelatedField):
        related_field_schema = field_to_schema(field.child_relation)

        return coreschema.Array(
            items=related_field_schema,
            title=title,
            description=description
        )
    elif isinstance(field, serializers.PrimaryKeyRelatedField):
        schema_cls = coreschema.String
        model = getattr(field.queryset, 'model', None)
        if model is not None:
            model_field = model._meta.pk
            if isinstance(model_field, models.AutoField):
                schema_cls = coreschema.Integer
        return schema_cls(title=title, description=description)
    elif isinstance(field, serializers.RelatedField):
        return coreschema.String(title=title, description=description)
    elif isinstance(field, serializers.MultipleChoiceField):
        return coreschema.Array(
            items=coreschema.Enum(enum=list(field.choices)),
            title=title,
            description=description
        )
    elif isinstance(field, serializers.ChoiceField):
        return coreschema.Enum(
            enum=list(field.choices),
            title=title,
            description=description
        )
    elif isinstance(field, serializers.BooleanField):
        return coreschema.Boolean(title=title, description=description)
    elif isinstance(field, (serializers.DecimalField, serializers.FloatField)):
        return coreschema.Number(title=title, description=description)
    elif isinstance(field, serializers.IntegerField):
        return coreschema.Integer(title=title, description=description)
    elif isinstance(field, serializers.DateField):
        return coreschema.String(
            title=title,
            description=description,
            format='date'
        )
    elif isinstance(field, serializers.DateTimeField):
        return coreschema.String(
            title=title,
            description=description,
            format='date-time'
        )
    elif isinstance(field, serializers.JSONField):
        return coreschema.Object(title=title, description=description)

    if field.style.get('base_template') == 'textarea.html':
        return coreschema.String(
            title=title,
            description=description,
            format='textarea'
        )

    return coreschema.String(title=title, description=description)
