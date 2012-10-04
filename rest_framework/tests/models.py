from django.db import models
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
        app_label = 'rest_framework'
        abstract = True


class Anchor(RESTFrameworkModel):
    text = models.CharField(max_length=100, default='anchor')


class BasicModel(RESTFrameworkModel):
    text = models.CharField(max_length=100)


class DefaultValueModel(RESTFrameworkModel):
    text = models.CharField(default='foobar', max_length=100)


class CallableDefaultValueModel(RESTFrameworkModel):
    text = models.CharField(default=foobar, max_length=100)


class ManyToManyModel(RESTFrameworkModel):
    rel = models.ManyToManyField(Anchor)
