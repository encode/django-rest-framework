"""
This test "app" exists to ensure that parts of Django REST Framework can be
imported/invoked before Django itself has been fully initialized.
"""

from rest_framework import compat, serializers  # noqa


# test initializing fields with lazy translations
class ExampleSerializer(serializers.Serializer):
    charfield = serializers.CharField(min_length=1, max_length=2)
    integerfield = serializers.IntegerField(min_value=1, max_value=2)
    floatfield = serializers.FloatField(min_value=1, max_value=2)
    decimalfield = serializers.DecimalField(max_digits=10, decimal_places=1, min_value=1, max_value=2)
    durationfield = serializers.DurationField(min_value=1, max_value=2)
    listfield = serializers.ListField(min_length=1, max_length=2)
