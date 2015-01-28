from rest_framework import serializers


class LinkSerializer(serializers.Serializer):
    name = serializers.CharField()
    next = serializers.RecursiveField(required=False, allow_null=True)


class NodeSerializer(serializers.Serializer):
    name = serializers.CharField()
    children = serializers.ListField(child=serializers.RecursiveField())


class TestRecursiveField:
    @staticmethod
    def serialize(serializer_class, value):
        serializer = serializer_class(value)

        assert serializer.data == value, \
            'serialized data does not match input'

    @staticmethod
    def deserialize(serializer_class, data):
        serializer = serializer_class(data=data)

        assert serializer.is_valid(), \
            'cannot validate on deserialization: %s' % dict(serializer.errors)
        assert serializer.validated_data == data, \
            'deserialized data does not match input'
        
    def test_link_serializer(self):
        value = {
            'name': 'first',
            'next': {
                'name': 'second',
                'next': {
                    'name': 'third',
                    'next': None,
                }
            }
        }

        self.serialize(LinkSerializer, value)
        self.deserialize(LinkSerializer, value)

    def test_node_serializer(self):
        value = {
            'name': 'root',
            'children': [{
                'name': 'first child',
                'children': [],
            }, {
                'name': 'second child',
                'children': [],
            }]
        }

        self.serialize(NodeSerializer, value)
        self.deserialize(NodeSerializer, value)
