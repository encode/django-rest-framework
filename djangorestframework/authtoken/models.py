import uuid
import hmac
from hashlib import sha1
from django.db import models


class Token(models.Model):
    """
    The default authorization token model.
    """
    key = models.CharField(max_length=40, primary_key=True)
    user = models.ForeignKey('auth.User')
    revoked = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super(Token, self).save(*args, **kwargs)

    def generate_key(self):
        unique = str(uuid.uuid4())
        return hmac.new(unique, digestmod=sha1).hexdigest()
