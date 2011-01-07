from rest.resource import Resource, ModelResource
from testapp.forms import ExampleForm
from testapp.models import ExampleModel, ExampleContainer, BlogPost, Comment
 
class RootResource(Resource):
    """This is my docstring
    """
    allowed_operations = ('read',)

    def read(self, headers={}, *args, **kwargs):
        return (200, {'read-only-api': self.reverse(ReadOnlyResource),
                      'write-only-api': self.reverse(WriteOnlyResource),
                      'read-write-api': self.reverse(ReadWriteResource),
                      'model-api': self.reverse(ModelFormResource),
                      'create-container': self.reverse(ContainerFactory),
                      'blog-post-creator': self.reverse(BlogPostCreator)}, {})


class ReadOnlyResource(Resource):
    """This is my docstring
    """
    allowed_operations = ('read',)

    def read(self, headers={}, *args, **kwargs):
        return (200, {'ExampleString': 'Example',
                      'ExampleInt': 1,
                      'ExampleDecimal': 1.0}, {})


class WriteOnlyResource(Resource):
    """This is my docstring
    """
    allowed_operations = ('update',)

    def update(self, data, headers={}, *args, **kwargs):
        return (200, data, {})


class ReadWriteResource(Resource):
    allowed_operations = ('read', 'update', 'delete')
    create_form = ExampleForm
    update_form = ExampleForm


class ModelFormResource(ModelResource):
    allowed_operations = ('read', 'update', 'delete')
    model = ExampleModel

# Nice things: form validation is applied to any input type
#              html forms for output
#              output always serialized nicely
class ContainerFactory(ModelResource):
    allowed_operations = ('create',)
    model = ExampleContainer
    fields = ('absolute_uri', 'name', 'key')
    form_fields = ('name',)


class ContainerInstance(ModelResource):
    allowed_operations = ('read', 'update', 'delete')
    model = ExampleContainer
    fields = ('absolute_uri', 'name', 'key')
    form_fields = ('name',)

#######################

    
class BlogPostCreator(ModelResource):
    """A Resource with which blog posts may be created.
    This is distinct from blog post instance so that it is discoverable by the client.
    (ie the client doens't need to know how to form a blog post url in order to create a blog post)"""
    allowed_operations = ('create',)
    model = BlogPost
    
class BlogPostInstance(ModelResource):
    """Represents a single Blog Post."""
    allowed_operations = ('read', 'update', 'delete')
    model = BlogPost