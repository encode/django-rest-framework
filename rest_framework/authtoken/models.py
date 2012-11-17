import uuid
import hmac
from hashlib import sha1
from django.db import models
from django import VERSION

try:
    from django.db.models.auth import User
    user_model = User
except ImportError:
    raise ImportError
else:
    raise

if VERSION[:2] in ((1, 5,),):
    from django.conf import settings
    if hasattr(settings, AUTH_USER_MODEL):
        user_model = settings.AUTH_USER_MODEL
    

class Token(models.Model):
    """
    The default authorization token model.
    """
    key = models.CharField(max_length=40, primary_key=True)
    user = models.OneToOneField(user_model, related_name='auth_token')
    created = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super(Token, self).save(*args, **kwargs)

    def generate_key(self):
        unique = str(uuid.uuid4())
        return hmac.new(unique, digestmod=sha1).hexdigest()

    def __unicode__(self):
        return self.key
