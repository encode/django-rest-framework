from __future__ import unicode_literals
from django.db import models
from django.test import TestCase
from rest_framework import serializers
from rest_framework.tests.models import RESTFrameworkModel


# Models
class ParentModel(RESTFrameworkModel):
    name1 = models.CharField(max_length=100)


class ChildModel(ParentModel):
    name2 = models.CharField(max_length=100)


class AssociatedModel(RESTFrameworkModel):
    ref = models.OneToOneField(ParentModel, primary_key=True)
    name = models.CharField(max_length=100)


# Serializers
class DerivedModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChildModel


class AssociatedModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssociatedModel


# Tests
class IneritedModelSerializationTests(TestCase):

    def test_multitable_inherited_model_fields_as_expected(self):
        """
        Assert that the parent pointer field is not included in the fields
        serialized fields
        """
        child = ChildModel(name1='parent name', name2='child name')
        serializer = DerivedModelSerializer(child)
        self.assertEqual(set(serializer.data.keys()),
                         set(['name1', 'name2', 'id']))

    def test_onetoone_primary_key_model_fields_as_expected(self):
        """
        Assert that a model with a onetoone field that is the primary key is
        not treated like a derived model
        """
        parent = ParentModel(name1='parent name')
        associate = AssociatedModel(name='hello', ref=parent)
        serializer = AssociatedModelSerializer(associate)
        self.assertEqual(set(serializer.data.keys()),
                         set(['name', 'ref']))

    def test_data_is_valid_without_parent_ptr(self):
        """
        Assert that the pointer to the parent table is not a required field
        for input data
        """
        data = {
            'name1': 'parent name',
            'name2': 'child name',
        }
        serializer = DerivedModelSerializer(data=data)
        self.assertEqual(serializer.is_valid(), True)
