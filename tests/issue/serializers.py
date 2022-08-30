from rest_framework import serializers

from . import models


class ItemAmountSerializer(serializers.ModelSerializer):
    item = serializers.PrimaryKeyRelatedField(queryset=models.Item.objects.all())

    class Meta:
        model = models.ItemAmount
        fields = ('item', 'amount')


class SummarySerializer(serializers.ModelSerializer):
    items = ItemAmountSerializer(source='itemamount_set', many=True)

    def create(self, validated_data):
        items = validated_data.pop('itemamount_set')
        instance = super().create(validated_data)
        for item in items:
            instance.items.add(
                item['item'], through_defaults=dict(
                    amount=item['amount']
                )
            )
        return instance

    class Meta:
        model = models.Summary
        fields = ('items', )
