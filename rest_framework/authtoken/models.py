import secrets

from django.conf import settings
from django.db import models
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
        For existing tokens with cleared keys, regenerates the key.
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
        """
        Generate a cryptographically secure token key.
        
        Uses secrets.token_hex(20) which provides 40 hexadecimal characters
        (160 bits of entropy) suitable for authentication tokens.
        
        Returns:
            str: A 40-character hexadecimal string
        """
        return secrets.token_hex(20)

    def __str__(self):
        return self.key


class TokenProxy(Token):
    """
    Proxy mapping pk to user pk for use in admin.
    """
    @property
    def pk(self):
        return self.user_id

    class Meta:
        proxy = 'rest_framework.authtoken' in settings.INSTALLED_APPS
        abstract = 'rest_framework.authtoken' not in settings.INSTALLED_APPS
        verbose_name = _("Token")
        verbose_name_plural = _("Tokens")
