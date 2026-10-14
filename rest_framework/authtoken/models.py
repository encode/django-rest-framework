import secrets

from django.conf import settings
from django.db import models, router
from django.utils.translation import gettext_lazy as _


class Token(models.Model):
    """
    The default authorization token model.
    """
    key = models.CharField(_("Key"), max_length=40, primary_key=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, related_name='auth_token',
        on_delete=models.CASCADE, verbose_name=_("User")
    )
    created = models.DateTimeField(_("Created"), auto_now_add=True)

    class Meta:
        # Work around for a bug in Django:
        # https://code.djangoproject.com/ticket/19422
        #
        # Also see corresponding ticket:
        # https://github.com/encode/django-rest-framework/issues/705
        abstract = 'rest_framework.authtoken' not in settings.INSTALLED_APPS
        verbose_name = _("Token")
        verbose_name_plural = _("Tokens")

    def save(self, *args, **kwargs):
        """
        Save the token instance.

        If no key is provided, generates a cryptographically secure key.
        For new tokens, ensures they are inserted as new (not updated).
        """
        if not self.key:
            self.key = self.generate_key()
            # For new objects, force INSERT to prevent overwriting existing tokens
            if self._state.adding:
                kwargs['force_insert'] = True
        return super().save(*args, **kwargs)

    @classmethod
    def generate_key(cls):
        return secrets.token_hex(20)

    def __str__(self):
        return self.key


class TokenProxyQuerySet(models.QuerySet):
    """
    Deletes through the concrete `Token`: the collector deletes by `pk`,
    which the proxy maps to the user id.
    """
    def delete(self):
        self._not_support_combined_queries('delete')
        if self.query.is_sliced:
            raise TypeError("Cannot use 'limit' or 'offset' with delete().")
        if self.query.distinct or self.query.distinct_fields:
            raise TypeError("Cannot call delete() after .distinct().")
        if self._fields is not None:
            raise TypeError(
                "Cannot call delete() after .values() or .values_list()"
            )
        # Ensure `self.db` resolves with the write routers, like the `QuerySet.delete()`
        self._for_write = True
        keys = list(self.values_list('pk', flat=True))
        return Token.objects.using(self.db).filter(pk__in=keys).delete()
    delete.alters_data = True
    delete.queryset_only = True


class TokenProxy(Token):
    """
    Proxy mapping pk to user pk for use in admin.
    """
    objects = TokenProxyQuerySet.as_manager()

    @property
    def pk(self):
        return self.user_id

    def delete(self, using=None, keep_parents=False):
        """
        Deletes through the concrete `Token`. The inherited delete matches
        the `key` column against `pk` -- a user id here -- and silently
        deletes nothing.
        """
        if self.key is None:
            raise ValueError(
                "%s object can't be deleted because its %s attribute is set "
                "to None." % (self._meta.object_name, self._meta.pk.attname)
            )
        # Resolve `using` in same order as in the base `Model.delete()`
        using = using or router.db_for_write(self.__class__, instance=self)
        deleted = type(self).objects.using(using).filter(key=self.key).delete()
        # `Model.delete()` clears the pk of the in-memory instance
        self.key = None
        return deleted

    class Meta:
        proxy = 'rest_framework.authtoken' in settings.INSTALLED_APPS
        abstract = 'rest_framework.authtoken' not in settings.INSTALLED_APPS
        verbose_name = _("Token")
        verbose_name_plural = _("Tokens")
