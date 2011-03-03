""""""
from django.db import models
from django.contrib.auth import Permission, User

class PermissionSet(models.Model):
    """"""
    name = models.CharField(unique=True, max_length=64)
    description = models.CharField(max_length=512)
    permissions = models.ManyToManyField(Permission, blank=True)


class UserToken(models.Model):
    """"""
    token_key = models.CharField(max_length=30, unique=True)
    token_secret = models.CharField(max_length=256)
    user = models.ForeignKey(User)
    permission_set = models.ForeignKey(PermissionSet, null=True, blank=True, help_text="If set then determines the subset of permissions that are granted by this token, rathen than granting full user permissions.")
    expiry = models.DateTimeField(default=None, blank=True, null=True, help_text="If set then determines when the token will no longer be treated as valid.  If left empty the token will not expire.")
    is_active = models.BooleanField(default=True)
