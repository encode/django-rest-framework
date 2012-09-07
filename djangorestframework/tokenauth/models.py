import uuid
from django.db import models

class BasicToken(models.Model):
    """
    The default authorization token model class.
    """
    key = models.CharField(max_length=32, primary_key=True, blank=True)
    user = models.ForeignKey('auth.User')
    revoked = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = uuid.uuid4().hex
        return super(BasicToken, self).save(*args, **kwargs)
