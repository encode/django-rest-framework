from rest.resource import Resource

class RootResource(Resource):
    """This is my docstring
    """

    def handle_get(self, headers={}, *args, **kwargs):
        return (200, {'Name': 'Test', 'Value': 1}, {'Location': 'BLAH'})
