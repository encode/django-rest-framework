import uuid
from django.db import models

class BaseToken(models.Model):
    """
    The base abstract authorization token model class.
    """
    key = models.CharField(max_length=32, primary_key=True, blank=True)
    user = models.ForeignKey('auth.User')
    revoked = models.BooleanField(default=False)

    class Meta:
        abstract=True

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = uuid.uuid4().hex
        return super(BaseToken, self).save(*args, **kwargs)


class Token(BaseToken):
    """
    The default authorization token model class.
    """
    pass
