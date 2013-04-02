from __future__ import unicode_literals
from django.test import TestCase
from django.db import models
from rest_framework import serializers
from rest_framework.relations import RecursiveRelatedField


class TreeModel(models.Model):

    name = models.CharField(max_length=127)
    parent = models.ForeignKey('self', null=True, related_name='children')

    def __unicode__(self):
        return self.name


class TreeSerializer(serializers.ModelSerializer):

    children = RecursiveRelatedField(many=True)

    class Meta:
        model = TreeModel
        exclude = ('id', )


class ChainModel(models.Model):

    name = models.CharField(max_length=127)
    previous = models.OneToOneField('self', null=True, related_name='next')

    def __unicode__(self):
        return self.name


class ChainSerializer(serializers.ModelSerializer):

    next = RecursiveRelatedField(many=False)

    class Meta:
        model = ChainModel
        exclude = ('id', )


class TestRecursiveRelatedField(TestCase):

    def setUp(self):
        self.tree_root = TreeModel.objects.create(name='Tree Root')
        tree_depth_1_children = []

        for x in range(0, 3):
            tree_depth_1_children.append(TreeModel.objects.create(name='Child 1:%d' % x, parent=self.tree_root))

        for x in range(0, 2):
            TreeModel.objects.create(name='Child 2:%d' % x, parent=tree_depth_1_children[1])

        self.chain_root = ChainModel.objects.create(name='Chain Root')
        current = self.chain_root
        for x in range(0, 3):
            chain_link = ChainModel.objects.create(name='Chain link %d' % x, previous=current)
            current = chain_link


    def test_many(self):
        serializer = TreeSerializer(self.tree_root)
        expected = {
            'children': [
                {
                    'children': [],
                    'name': 'Child 1:0',
                    'parent': 1
                },
                {
                    'children': [
                        {
                            'children': [],
                            'name': 'Child 2:0',
                            'parent': 3
                        },
                        {
                            'children': [],
                            'name': 'Child 2:1',
                            'parent': 3
                        }
                    ],
                    'name': 'Child 1:1',
                    'parent': 1
                },
                {
                    'children': [],
                    'name': 'Child 1:2',
                    'parent': 1
                }
            ],
            'name': 'Tree Root',
            'parent': None
        }
        self.assertEqual(serializer.data, expected)

    def test_one(self):
        serializer = ChainSerializer(self.chain_root)
        expected = {
            'next':
                {
                    'next':
                        {'next':
                             {'next':  None,
                              'name': 'Chain link 2',
                              'previous': 3},
                         'name': 'Chain link 1',
                         'previous': 2},
                    'name': 'Chain link 0',
                    'previous': 1},
            'name': 'Chain Root',
            'previous': None
        }
        self.assertEqual(serializer.data, expected)

