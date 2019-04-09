# coding: utf-8
from __future__ import unicode_literals

from django.conf import settings
from django.db import models


class CustomToken(models.Model):
    key = models.CharField(max_length=40, primary_key=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
