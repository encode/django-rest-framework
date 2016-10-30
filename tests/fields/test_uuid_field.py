import uuid

from rest_framework import serializers
from .base import FieldValues


class TestUUIDField(FieldValues):
    """
    Valid and invalid values for `UUIDField`.
    """
    valid_inputs = {
        '825d7aeb-05a9-45b5-a5b7-05df87923cda': uuid.UUID('825d7aeb-05a9-45b5-a5b7-05df87923cda'),
        '825d7aeb05a945b5a5b705df87923cda': uuid.UUID('825d7aeb-05a9-45b5-a5b7-05df87923cda'),
        'urn:uuid:213b7d9b-244f-410d-828c-dabce7a2615d': uuid.UUID('213b7d9b-244f-410d-828c-dabce7a2615d'),
        284758210125106368185219588917561929842: uuid.UUID('d63a6fb6-88d5-40c7-a91c-9edf73283072')
    }
    invalid_inputs = {
        '825d7aeb-05a9-45b5-a5b7': ['"825d7aeb-05a9-45b5-a5b7" is not a valid UUID.'],
        (1, 2, 3): ['"(1, 2, 3)" is not a valid UUID.']
    }
    outputs = {
        uuid.UUID('825d7aeb-05a9-45b5-a5b7-05df87923cda'): '825d7aeb-05a9-45b5-a5b7-05df87923cda'
    }
    field = serializers.UUIDField()

    def _test_format(self, uuid_format, formatted_uuid_0):
        field = serializers.UUIDField(format=uuid_format)
        assert field.to_representation(uuid.UUID(int=0)) == formatted_uuid_0
        assert field.to_internal_value(formatted_uuid_0) == uuid.UUID(int=0)

    def test_formats(self):
        self._test_format('int', 0)
        self._test_format('hex_verbose', '00000000-0000-0000-0000-000000000000')
        self._test_format('urn', 'urn:uuid:00000000-0000-0000-0000-000000000000')
        self._test_format('hex', '0' * 32)
