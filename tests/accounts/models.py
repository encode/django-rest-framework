from django.db import models

from tests.users.models import User


class Account(models.Model):
    owner = models.ForeignKey(User, related_name='accounts_owned')
    admins = models.ManyToManyField(User, blank=True, null=True, related_name='accounts_administered')
