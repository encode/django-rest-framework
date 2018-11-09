from __future__ import unicode_literals

import uuid

from django.db import models
from django.utils.translation import ugettext_lazy as _


class RESTFrameworkModel(models.Model):
    """
    Base for test models that sets app_label, so they play nicely.
    """

    class Meta:
        app_label = 'tests'
        abstract = True


class BasicModel(RESTFrameworkModel):
    text = models.CharField(
        max_length=100,
        verbose_name=_("Text comes here"),
        help_text=_("Text description.")
    )


# Models for relations tests
# ManyToMany
class ManyToManyTarget(RESTFrameworkModel):
    name = models.CharField(max_length=100)


class ManyToManySource(RESTFrameworkModel):
    name = models.CharField(max_length=100)
    targets = models.ManyToManyField(ManyToManyTarget, related_name='sources')


# ForeignKey
class ForeignKeyTarget(RESTFrameworkModel):
    name = models.CharField(max_length=100)


class UUIDForeignKeyTarget(RESTFrameworkModel):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=100)


class ForeignKeySource(RESTFrameworkModel):
    name = models.CharField(max_length=100)
    target = models.ForeignKey(ForeignKeyTarget, related_name='sources',
                               help_text='Target', verbose_name='Target',
                               on_delete=models.CASCADE)


# Nullable ForeignKey
class NullableForeignKeySource(RESTFrameworkModel):
    name = models.CharField(max_length=100)
    target = models.ForeignKey(ForeignKeyTarget, null=True, blank=True,
                               related_name='nullable_sources',
                               verbose_name='Optional target object',
                               on_delete=models.CASCADE)


class NullableUUIDForeignKeySource(RESTFrameworkModel):
    name = models.CharField(max_length=100)
    target = models.ForeignKey(ForeignKeyTarget, null=True, blank=True,
                               related_name='nullable_sources',
                               verbose_name='Optional target object',
                               on_delete=models.CASCADE)


class NestedForeignKeySource(RESTFrameworkModel):
    """
    Used for testing FK chain. A -> B -> C.
    """
    name = models.CharField(max_length=100)
    target = models.ForeignKey(NullableForeignKeySource, null=True, blank=True,
                               related_name='nested_sources',
                               verbose_name='Intermediate target object',
                               on_delete=models.CASCADE)


# OneToOne
class OneToOneTarget(RESTFrameworkModel):
    name = models.CharField(max_length=100)


class NullableOneToOneSource(RESTFrameworkModel):
    name = models.CharField(max_length=100)
    target = models.OneToOneField(
        OneToOneTarget, null=True, blank=True,
        related_name='nullable_source', on_delete=models.CASCADE)


class OneToOnePKSource(RESTFrameworkModel):
    """ Test model where the primary key is a OneToOneField with another model. """
    name = models.CharField(max_length=100)
    target = models.OneToOneField(
        OneToOneTarget, primary_key=True,
        related_name='required_source', on_delete=models.CASCADE)
