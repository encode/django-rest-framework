from django.test import TestCase

from rest_framework import serializers

from .models import (
    ForeignKeySource,
    ForeignKeyTarget,
    ForeignKeySourceWithLimitedChoices,
)


class ForeignKeySourceWithLimitedChoicesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForeignKeySourceWithLimitedChoices
        fields = ("id", "target")


class ForeignKeySourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForeignKeySource
        fields = ("id", "target")


class LimitedChoicesInQuerySetTests(TestCase):
    def setUp(self):
        for idx in range(1, 4):
            limited_target = ForeignKeyTarget(name="limited-target-%d" % idx)
            limited_target.save()
            target = ForeignKeyTarget(name="target-%d" % idx)
            target.save()

    def test_queryset_size_without_limited_choices(self):
        queryset = ForeignKeySourceSerializer().fields["target"].get_queryset()
        assert len(queryset) == 6

    def test_queryset_size_with_limited_choices(self):
        queryset = ForeignKeySourceWithLimitedChoicesSerializer().fields["target"].get_queryset()
        assert len(queryset) == 3
