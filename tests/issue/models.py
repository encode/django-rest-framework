from django.db import models


class Item(models.Model):
    name = models.CharField(max_length=10)


class ItemAmount(models.Model):
    summary = models.ForeignKey('Summary', on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    amount = models.IntegerField()


class Summary(models.Model):
    items = models.ManyToManyField(Item, through=ItemAmount)
