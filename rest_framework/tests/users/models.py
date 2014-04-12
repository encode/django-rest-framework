from django.db import models


class User(models.Model):
    account = models.ForeignKey('accounts.Account', blank=True, null=True, related_name='users')
    active_record = models.ForeignKey('records.Record', blank=True, null=True)
