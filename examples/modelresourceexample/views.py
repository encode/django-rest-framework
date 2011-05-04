from djangorestframework.modelresource import InstanceModelResource, ListOrCreateModelResource
from modelresourceexample.models import MyModel

FIELDS = ('foo', 'bar', 'baz', 'absolute_url')

class MyModelRootResource(ListOrCreateModelResource):
    """A create/list resource for MyModel.
    Available for both authenticated and anonymous access for the purposes of the sandbox."""
    model = MyModel
    fields = FIELDS

class MyModelResource(InstanceModelResource):
    """A read/update/delete resource for MyModel.
    Available for both authenticated and anonymous access for the purposes of the sandbox."""
    model = MyModel
    fields = FIELDS
