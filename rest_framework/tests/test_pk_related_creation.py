from django.db import models
from rest_framework import serializers

from django.test import TestCase


class TestModel(models.Model):

    class Meta:
        app_label = 'tests'


class Person(TestModel):
    name = models.CharField(max_length=200)


class Group(TestModel):
    name = models.TextField()
    members = models.ManyToManyField(Person)


class GroupSerialiser(serializers.ModelSerializer):

    members = serializers.PrimaryKeyRelatedField(many=True)

    class Meta:
        model = Group
        fields = (
            'id',
            'name',
            'members'
        )


class TestPrimaryKeyRelatedRelation(TestCase):

    def test_deserialize_group(self):

        person = Person.objects.create(name='Person')
        data = {
            'name': 'Group Name',
            'members': [person.id]
        }

        serializer = GroupSerialiser(data=data, files=None)

        self.assertTrue(serializer.is_valid())

        obj = serializer.object

        self.assertEqual(obj.members, [person])
