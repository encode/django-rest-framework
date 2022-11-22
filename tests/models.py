import uuid

from django.contrib.auth.models import User
from django.db import models
from django.db.models import QuerySet
from django.db.models.manager import BaseManager
from django.utils.translation import gettext_lazy as _


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


class BasicModelWithUsers(RESTFrameworkModel):
    users = models.ManyToManyField(User)


# ForeignKey
class ForeignKeyTarget(RESTFrameworkModel):
    name = models.CharField(max_length=100)

    def get_first_source(self):
        """Used for testing related field against a callable."""
        return self.sources.all().order_by('pk')[0]

    @property
    def first_source(self):
        """Used for testing related field against a property."""
        return self.sources.all().order_by('pk')[0]


class UUIDForeignKeyTarget(RESTFrameworkModel):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=100)


class ForeignKeySource(RESTFrameworkModel):
    name = models.CharField(max_length=100)
    target = models.ForeignKey(ForeignKeyTarget, related_name='sources',
                               help_text='Target', verbose_name='Target',
                               on_delete=models.CASCADE)


class ForeignKeySourceWithLimitedChoices(RESTFrameworkModel):
    target = models.ForeignKey(ForeignKeyTarget, help_text='Target',
                               verbose_name='Target',
                               limit_choices_to={"name__startswith": "limited-"},
                               on_delete=models.CASCADE)


class ForeignKeySourceWithQLimitedChoices(RESTFrameworkModel):
    target = models.ForeignKey(ForeignKeyTarget, help_text='Target',
                               verbose_name='Target',
                               limit_choices_to=models.Q(name__startswith="limited-"),
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


class CustomManagerModel(RESTFrameworkModel):
    class CustomManager:
        def __new__(cls, *args, **kwargs):
            cls = BaseManager.from_queryset(
                QuerySet
            )
            return cls

    objects = CustomManager()()
    # `CustomManager()` will return a `BaseManager` class.
    # We need to instantiation it, so we write `CustomManager()()` here.

    text = models.CharField(
        max_length=100,
        verbose_name=_("Text comes here"),
        help_text=_("Text description.")
    )

    o2o_target = models.ForeignKey(OneToOneTarget,
                                   help_text='OneToOneTarget',
                                   verbose_name='OneToOneTarget',
                                   on_delete=models.CASCADE)
