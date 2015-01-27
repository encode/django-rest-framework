from rest_framework import serializers

class LinkSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=25)
    next = serializers.RecursiveField(required=False, allow_null=True)


class NodeSerializer(serializers.Serializer):
    name = serializers.CharField()
    children = serializers.ListField(child=serializers.RecursiveField())


class PingSerializer(serializers.Serializer):
    ping_id = serializers.IntegerField()
    pong = serializers.RecursiveField('PongSerializer', required=False)


class PongSerializer(serializers.Serializer):
    pong_id = serializers.IntegerField()
    ping = PingSerializer()


class SillySerializer(serializers.Serializer):
    name = serializers.RecursiveField(
        'CharField', 'rest_framework.fields', max_length=5)
    blankable = serializers.RecursiveField(
        'CharField', 'rest_framework.fields', allow_blank=True)
    nullable = serializers.RecursiveField(
        'CharField', 'rest_framework.fields', allow_null=True)
    links = serializers.RecursiveField('LinkSerializer')
    self = serializers.RecursiveField(required=False)

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

    def test_ping_pong(self):
        pong = {
            'pong_id': 4,
            'ping': {
                'ping_id': 3,
                'pong': {
                    'pong_id': 2,
                    'ping': {
                        'ping_id': 1,
                    },
                },
            },
        }
        self.serialize(PongSerializer, pong)
        self.deserialize(PongSerializer, pong)

    def test_validation(self):
        value = {
            'name': 'good',
            'blankable': '',
            'nullable': None,
            'links': {
                'name': 'something',
                'next': {
                    'name': 'inner something',
                }
            }
        }
        self.serialize(SillySerializer, value)
        self.deserialize(SillySerializer, value)

        max_length = {
            'name': 'too long',
            'blankable': 'not blank',
            'nullable': 'not null',
            'links': {
                'name': 'something',
            }
        }
        serializer = SillySerializer(data=max_length)
        assert not serializer.is_valid(), \
            'validation should fail due to name too long'

        nulled_out = {
            'name': 'good',
            'blankable': None,
            'nullable': 'not null',
            'links': {
                'name': 'something',
            }
        }
        serializer = SillySerializer(data=nulled_out)
        assert not serializer.is_valid(), \
            'validation should fail due to null field'

        way_too_long = {
            'name': 'good',
            'blankable': '',
            'nullable': None,
            'links': {
                'name': 'something',
                'next': {
                    'name': 'inner something that is much too long',
                }
            }
        }
        serializer = SillySerializer(data=way_too_long)
        assert not serializer.is_valid(), \
            'validation should fail on inner link validation'
