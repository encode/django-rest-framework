"""
Helper function for returning the field information that is associated
with a model class. This includes returning all the forward and reverse
relationships and their associated metadata.

Usage: `get_field_info(model)` returns a `FieldInfo` instance.
"""
import inspect
from collections import namedtuple

from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.utils import six

from rest_framework.compat import OrderedDict

FieldInfo = namedtuple('FieldResult', [
    'pk',  # Model field instance
    'fields',  # Dict of field name -> model field instance
    'forward_relations',  # Dict of field name -> RelationInfo
    'reverse_relations',  # Dict of field name -> RelationInfo
    'fields_and_pk',  # Shortcut for 'pk' + 'fields'
    'relations'  # Shortcut for 'forward_relations' + 'reverse_relations'
])

RelationInfo = namedtuple('RelationInfo', [
    'model_field',
    'related_model',
    'to_many',
    'has_through_model'
])


def _resolve_model(obj):
    """
    Resolve supplied `obj` to a Django model class.

    `obj` must be a Django model class itself, or a string
    representation of one.  Useful in situations like GH #1225 where
    Django may not have resolved a string-based reference to a model in
    another model's foreign key definition.

    String representations should have the format:
        'appname.ModelName'
    """
    if isinstance(obj, six.string_types) and len(obj.split('.')) == 2:
        app_name, model_name = obj.split('.')
        resolved_model = models.get_model(app_name, model_name)
        if resolved_model is None:
            msg = "Django did not return a model for {0}.{1}"
            raise ImproperlyConfigured(msg.format(app_name, model_name))
        return resolved_model
    elif inspect.isclass(obj) and issubclass(obj, models.Model):
        return obj
    raise ValueError("{0} is not a Django model".format(obj))


def get_field_info(model):
    """
    Given a model class, returns a `FieldInfo` instance, which is a
    `namedtuple`, containing metadata about the various field types on the model
    including information about their relationships.
    """
    opts = model._meta.concrete_model._meta

    pk = _get_pk(opts)
    fields = _get_fields(opts)
    forward_relations = _get_forward_relationships(opts)
    reverse_relations = _get_reverse_relationships(opts)
    fields_and_pk = _merge_fields_and_pk(pk, fields)
    relationships = _merge_relationships(forward_relations, reverse_relations)

    return FieldInfo(pk, fields, forward_relations, reverse_relations,
                     fields_and_pk, relationships)


def _get_pk(opts):
    pk = opts.pk
    while pk.rel and pk.rel.parent_link:
        # If model is a child via multi-table inheritance, use parent's pk.
        pk = pk.rel.to._meta.pk

    return pk


def _get_fields(opts):
    fields = OrderedDict()
    for field in [field for field in opts.fields if field.serialize and not field.rel]:
        fields[field.name] = field

    return fields


def _get_forward_relationships(opts):
    """
    Returns an `OrderedDict` of field names to `RelationInfo`.
    """
    forward_relations = OrderedDict()
    for field in [field for field in opts.fields if field.serialize and field.rel]:
        forward_relations[field.name] = RelationInfo(
            model_field=field,
            related_model=_resolve_model(field.rel.to),
            to_many=False,
            has_through_model=False
        )

    # Deal with forward many-to-many relationships.
    for field in [field for field in opts.many_to_many if field.serialize]:
        forward_relations[field.name] = RelationInfo(
            model_field=field,
            related_model=_resolve_model(field.rel.to),
            to_many=True,
            has_through_model=(
                not field.rel.through._meta.auto_created
            )
        )

    return forward_relations


def _get_reverse_relationships(opts):
    """
    Returns an `OrderedDict` of field names to `RelationInfo`.
    """
    # Note that we have a hack here to handle internal API differences for
    # this internal API across Django 1.7 -> Django 1.8.
    # See: https://code.djangoproject.com/ticket/24208

    reverse_relations = OrderedDict()
    for relation in opts.get_all_related_objects():
        accessor_name = relation.get_accessor_name()
        related = getattr(relation, 'related_model', relation.model)
        reverse_relations[accessor_name] = RelationInfo(
            model_field=None,
            related_model=related,
            to_many=relation.field.rel.multiple,
            has_through_model=False
        )

    # Deal with reverse many-to-many relationships.
    for relation in opts.get_all_related_many_to_many_objects():
        accessor_name = relation.get_accessor_name()
        related = getattr(relation, 'related_model', relation.model)
        reverse_relations[accessor_name] = RelationInfo(
            model_field=None,
            related_model=related,
            to_many=True,
            has_through_model=(
                (getattr(relation.field.rel, 'through', None) is not None) and
                not relation.field.rel.through._meta.auto_created
            )
        )

    return reverse_relations


def _merge_fields_and_pk(pk, fields):
    fields_and_pk = OrderedDict()
    fields_and_pk['pk'] = pk
    fields_and_pk[pk.name] = pk
    fields_and_pk.update(fields)

    return fields_and_pk


def _merge_relationships(forward_relations, reverse_relations):
    return OrderedDict(
        list(forward_relations.items()) +
        list(reverse_relations.items())
    )


def is_abstract_model(model):
    """
    Given a model class, returns a boolean True if it is abstract and False if it is not.
    """
    return hasattr(model, '_meta') and hasattr(model._meta, 'abstract') and model._meta.abstract
