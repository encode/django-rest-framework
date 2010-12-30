from rest.resource import Resource

class RootResource(Resource):
    """This is my docstring
    """
    allowed_methods = ('GET',)

    def read(self, headers={}, *args, **kwargs):
        return (200, {'read-only-api': self.reverse(ReadOnlyResource),
                      'write-only-api': self.reverse(MirroringWriteResource)}, {})


class ReadOnlyResource(Resource):
    """This is my docstring
    """
    allowed_methods = ('GET',)

    def read(self, headers={}, *args, **kwargs):
        return (200, {'ExampleString': 'Example',
                      'ExampleInt': 1,
                      'ExampleDecimal': 1.0}, {})


class MirroringWriteResource(Resource):
    """This is my docstring
    """
    allowed_methods = ('PUT',)

    def create(self, data, headers={}, *args, **kwargs):
        return (200, data, {})
