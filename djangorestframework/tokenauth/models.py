from django.db import models

class BaseToken(models.Model):
    """
    The base abstract authorization token model class.
    """
    key = models.CharField(max_length=32, primary_key=True)
    user = models.ForeignKey('auth.User')
    revoked = models.BooleanField(default=False)

    class Meta:
        abstract=True


class Token(BaseToken):
    """
    The default authorization token model class.
    """
    pass
