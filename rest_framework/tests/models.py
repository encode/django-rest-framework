from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import GenericForeignKey, GenericRelation

# from django.contrib.auth.models import Group


# class CustomUser(models.Model):
#     """
#     A custom user model, which uses a 'through' table for the foreign key
#     """
#     username = models.CharField(max_length=255, unique=True)
#     groups = models.ManyToManyField(
#         to=Group, blank=True, null=True, through='UserGroupMap'
#     )

#     @models.permalink
#     def get_absolute_url(self):
#         return ('custom_user', (), {
#             'pk': self.id
#     })


# class UserGroupMap(models.Model):
#     user = models.ForeignKey(to=CustomUser)
#     group = models.ForeignKey(to=Group)

#     @models.permalink
#     def get_absolute_url(self):
#         return ('user_group_map', (), {
#             'pk': self.id
#         })

def foobar():
    return 'foobar'


class RESTFrameworkModel(models.Model):
    """
    Base for test models that sets app_label, so they play nicely.
    """
    class Meta:
        app_label = 'tests'
        abstract = True


class Anchor(RESTFrameworkModel):
    text = models.CharField(max_length=100, default='anchor')


class BasicModel(RESTFrameworkModel):
    text = models.CharField(max_length=100)


class SlugBasedModel(RESTFrameworkModel):
    text = models.CharField(max_length=100)
    slug = models.SlugField(max_length=32)


class DefaultValueModel(RESTFrameworkModel):
    text = models.CharField(default='foobar', max_length=100)


class CallableDefaultValueModel(RESTFrameworkModel):
    text = models.CharField(default=foobar, max_length=100)


class ManyToManyModel(RESTFrameworkModel):
    rel = models.ManyToManyField(Anchor)


class ReadOnlyManyToManyModel(RESTFrameworkModel):
    text = models.CharField(max_length=100, default='anchor')
    rel = models.ManyToManyField(Anchor)

# Models to test generic relations


class Tag(RESTFrameworkModel):
    tag_name = models.SlugField()


class TaggedItem(RESTFrameworkModel):
    tag = models.ForeignKey(Tag, related_name='items')
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        return self.tag.tag_name


class Bookmark(RESTFrameworkModel):
    url = models.URLField()
    tags = GenericRelation(TaggedItem)


# Model to test filtering.
class FilterableItem(RESTFrameworkModel):
    text = models.CharField(max_length=100)
    decimal = models.DecimalField(max_digits=4, decimal_places=2)
    date = models.DateField()


# Model for regression test for #285

class Comment(RESTFrameworkModel):
    email = models.EmailField()
    content = models.CharField(max_length=200)
    created = models.DateTimeField(auto_now_add=True)


class ActionItem(RESTFrameworkModel):
    title = models.CharField(max_length=200)
    done = models.BooleanField(default=False)


# Models for reverse relations
class BlogPost(RESTFrameworkModel):
    title = models.CharField(max_length=100)


class BlogPostComment(RESTFrameworkModel):
    text = models.TextField()
    blog_post = models.ForeignKey(BlogPost)


class Album(RESTFrameworkModel):
    title = models.CharField(max_length=100, unique=True)


class Photo(RESTFrameworkModel):
    description = models.TextField()
    album = models.ForeignKey(Album)


class Person(RESTFrameworkModel):
    name = models.CharField(max_length=10)
    age = models.IntegerField(null=True, blank=True)

    @property
    def info(self):
        return {
            'name': self.name,
            'age': self.age,
        }


# Model for issue #324
class BlankFieldModel(RESTFrameworkModel):
    title = models.CharField(max_length=100, blank=True)


# Model for issue #380
class OptionalRelationModel(RESTFrameworkModel):
    other = models.ForeignKey('OptionalRelationModel', blank=True, null=True)
