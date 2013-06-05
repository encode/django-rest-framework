from __future__ import unicode_literals
from django.db import models
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers


def foobar():
    return 'foobar'


class CustomField(models.CharField):

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 12
        super(CustomField, self).__init__(*args, **kwargs)


class RESTFrameworkModel(models.Model):
    """
    Base for test models that sets app_label, so they play nicely.
    """
    class Meta:
        app_label = 'tests'
        abstract = True


class HasPositiveIntegerAsChoice(RESTFrameworkModel):
    some_choices = ((1, 'A'), (2, 'B'), (3, 'C'))
    some_integer = models.PositiveIntegerField(choices=some_choices)


class Anchor(RESTFrameworkModel):
    text = models.CharField(max_length=100, default='anchor')


class BasicModel(RESTFrameworkModel):
    text = models.CharField(max_length=100, verbose_name=_("Text comes here"), help_text=_("Text description."))


class SlugBasedModel(RESTFrameworkModel):
    text = models.CharField(max_length=100)
    slug = models.SlugField(max_length=32)


class DefaultValueModel(RESTFrameworkModel):
    text = models.CharField(default='foobar', max_length=100)
    extra = models.CharField(blank=True, null=True, max_length=100)


class CallableDefaultValueModel(RESTFrameworkModel):
    text = models.CharField(default=foobar, max_length=100)


class ManyToManyModel(RESTFrameworkModel):
    rel = models.ManyToManyField(Anchor)


class ReadOnlyManyToManyModel(RESTFrameworkModel):
    text = models.CharField(max_length=100, default='anchor')
    rel = models.ManyToManyField(Anchor)


# Model for regression test for #285

class Comment(RESTFrameworkModel):
    email = models.EmailField()
    content = models.CharField(max_length=200)
    created = models.DateTimeField(auto_now_add=True)


class ActionItem(RESTFrameworkModel):
    title = models.CharField(max_length=200)
    done = models.BooleanField(default=False)
    info = CustomField(default='---', max_length=12)


# Models for reverse relations
class Person(RESTFrameworkModel):
    name = models.CharField(max_length=10)
    age = models.IntegerField(null=True, blank=True)

    @property
    def info(self):
        return {
            'name': self.name,
            'age': self.age,
        }


class BlogPost(RESTFrameworkModel):
    title = models.CharField(max_length=100)
    writer = models.ForeignKey(Person, null=True, blank=True)

    def get_first_comment(self):
        return self.blogpostcomment_set.all()[0]


class BlogPostComment(RESTFrameworkModel):
    text = models.TextField()
    blog_post = models.ForeignKey(BlogPost)


class Album(RESTFrameworkModel):
    title = models.CharField(max_length=100, unique=True)


class Photo(RESTFrameworkModel):
    description = models.TextField()
    album = models.ForeignKey(Album)


# Model for issue #324
class BlankFieldModel(RESTFrameworkModel):
    title = models.CharField(max_length=100, blank=True, null=False)


# Model for issue #380
class OptionalRelationModel(RESTFrameworkModel):
    other = models.ForeignKey('OptionalRelationModel', blank=True, null=True)


# Model for RegexField
class Book(RESTFrameworkModel):
    isbn = models.CharField(max_length=13)


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


class ForeignKeySource(RESTFrameworkModel):
    name = models.CharField(max_length=100)
    target = models.ForeignKey(ForeignKeyTarget, related_name='sources')


# Nullable ForeignKey
class NullableForeignKeySource(RESTFrameworkModel):
    name = models.CharField(max_length=100)
    target = models.ForeignKey(ForeignKeyTarget, null=True, blank=True,
                               related_name='nullable_sources')


# OneToOne
class OneToOneTarget(RESTFrameworkModel):
    name = models.CharField(max_length=100)


class NullableOneToOneSource(RESTFrameworkModel):
    name = models.CharField(max_length=100)
    target = models.OneToOneField(OneToOneTarget, null=True, blank=True,
                                  related_name='nullable_source')


# Serializer used to test BasicModel
class BasicModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = BasicModel
