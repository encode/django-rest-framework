from __future__ import unicode_literals
from django.db import models
from rest_framework.tests.models import RESTFrameworkModel


class ParentModel(RESTFrameworkModel):
    name1 = models.CharField(max_length=100)


class ChildModel(ParentModel):
    name2 = models.CharField(max_length=100)


class AssociatedModel(RESTFrameworkModel):
    ref = models.OneToOneField(ParentModel, primary_key=True)
    name = models.CharField(max_length=100)
