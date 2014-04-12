from django.db import models


class Record(models.Model):
    account = models.ForeignKey('accounts.Account', blank=True, null=True)
    owner = models.ForeignKey('users.User', blank=True, null=True)
