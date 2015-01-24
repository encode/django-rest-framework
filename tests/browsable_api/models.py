from django.db import models


class Foo(models.Model):
    name = models.CharField(max_length=30)


class Bar(models.Model):
    foo = models.ForeignKey("Foo", editable=False)
