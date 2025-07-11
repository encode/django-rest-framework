from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from guardian.compat import user_model_label
from guardian.ctypes import get_content_type
from guardian.managers import GroupObjectPermissionManager, UserObjectPermissionManager


class BaseObjectPermission(models.Model):
    """
    Abstract ObjectPermission class. Actual class should additionally define
    a ``content_object`` field and either ``user`` or ``group`` field.
    """
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    class Meta:
        abstract = True

    def __str__(self):
        return '{} | {} | {}'.format(
            str(self.content_object),
            str(getattr(self, 'user', False) or self.group),
            str(self.permission.codename))

    def save(self, *args, **kwargs):
        content_type = get_content_type(self.content_object)
        if content_type != self.permission.content_type:
            raise ValidationError("Cannot persist permission not designed for "
                                  "this class (permission's type is %r and object's type is %r)"
                                  % (self.permission.content_type, content_type))
        return super().save(*args, **kwargs)


class BaseGenericObjectPermission(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_pk = models.CharField(_('object ID'), max_length=255)
    content_object = GenericForeignKey(fk_field='object_pk')

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['content_type', 'object_pk']),
        ]


class UserObjectPermissionBase(BaseObjectPermission):
    """
    **Manager**: :manager:`UserObjectPermissionManager`
    """
    user = models.ForeignKey(user_model_label, on_delete=models.CASCADE)

    objects = UserObjectPermissionManager()

    class Meta:
        abstract = True
        unique_together = ['user', 'permission', 'content_object']


class UserObjectPermissionAbstract(UserObjectPermissionBase, BaseGenericObjectPermission):

    class Meta(UserObjectPermissionBase.Meta, BaseGenericObjectPermission.Meta):
        abstract = True
        unique_together = ['user', 'permission', 'object_pk']


class UserObjectPermission(UserObjectPermissionAbstract):

    class Meta(UserObjectPermissionAbstract.Meta):
        abstract = False


class GroupObjectPermissionBase(BaseObjectPermission):
    """
    **Manager**: :manager:`GroupObjectPermissionManager`
    """
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

    objects = GroupObjectPermissionManager()

    class Meta:
        abstract = True
        unique_together = ['group', 'permission', 'content_object']


class GroupObjectPermissionAbstract(GroupObjectPermissionBase, BaseGenericObjectPermission):

    class Meta(GroupObjectPermissionBase.Meta, BaseGenericObjectPermission.Meta):
        abstract = True
        unique_together = ['group', 'permission', 'object_pk']

class GroupObjectPermission(GroupObjectPermissionAbstract):

    class Meta(GroupObjectPermissionAbstract.Meta):
        abstract = False
