from rest.resource import Resource, ModelResource, QueryModelResource
from testapp.models import BlogPost, Comment
 
class RootResource(Resource):
    """This is the top level resource for the API.
    All the sub-resources are discoverable from here."""
    allowed_operations = ('read',)

    def read(self, headers={}, *args, **kwargs):
        return (200, {'blog-posts': self.reverse(BlogPostList),
                      'blog-post': self.reverse(BlogPostCreator)}, {})


# Blog Post Resources

class BlogPostList(QueryModelResource):
    """A resource which lists all existing blog posts."""
    allowed_operations = ('read', )
    model = BlogPost


class BlogPostCreator(ModelResource):
    """A resource with which blog posts may be created."""
    allowed_operations = ('create',)
    model = BlogPost
    fields = ('created', 'title', 'slug', 'content', 'absolute_url', 'comment_url', 'comments_url')


class BlogPostInstance(ModelResource):
    """A resource which represents a single blog post."""
    allowed_operations = ('read', 'update', 'delete')
    model = BlogPost
    fields = ('created', 'title', 'slug', 'content', 'absolute_url', 'comment_url', 'comments_url')


# Comment Resources

class CommentList(QueryModelResource):
    """A resource which lists all existing comments for a given blog post."""
    allowed_operations = ('read', )
    model = Comment


class CommentCreator(ModelResource):
    """A resource with which blog comments may be created for a given blog post."""
    allowed_operations = ('create',)
    model = Comment
    fields = ('username', 'comment', 'created', 'rating', 'absolute_url', 'blogpost_url')


class CommentInstance(ModelResource):
    """A resource which represents a single comment."""
    allowed_operations = ('read', 'update', 'delete')
    model = Comment
    fields = ('username', 'comment', 'created', 'rating', 'absolute_url', 'blogpost_url')
    
#
#'read-only-api': self.reverse(ReadOnlyResource),
#                      'write-only-api': self.reverse(WriteOnlyResource),
#                      'read-write-api': self.reverse(ReadWriteResource),
#                      'model-api': self.reverse(ModelFormResource),
#                      'create-container': self.reverse(ContainerFactory),
#
#class ReadOnlyResource(Resource):
#    """This is my docstring
#    """
#    allowed_operations = ('read',)
#
#    def read(self, headers={}, *args, **kwargs):
#        return (200, {'ExampleString': 'Example',
#                      'ExampleInt': 1,
#                      'ExampleDecimal': 1.0}, {})
#
#
#class WriteOnlyResource(Resource):
#    """This is my docstring
#    """
#    allowed_operations = ('update',)
#
#    def update(self, data, headers={}, *args, **kwargs):
#        return (200, data, {})
#
#
#class ReadWriteResource(Resource):
#    allowed_operations = ('read', 'update', 'delete')
#    create_form = ExampleForm
#    update_form = ExampleForm
#
#
#class ModelFormResource(ModelResource):
#    allowed_operations = ('read', 'update', 'delete')
#    model = ExampleModel
#
## Nice things: form validation is applied to any input type
##              html forms for output
##              output always serialized nicely
#class ContainerFactory(ModelResource):
#    allowed_operations = ('create',)
#    model = ExampleContainer
#    fields = ('absolute_uri', 'name', 'key')
#    form_fields = ('name',)
#
#
#class ContainerInstance(ModelResource):
#    allowed_operations = ('read', 'update', 'delete')
#    model = ExampleContainer
#    fields = ('absolute_uri', 'name', 'key')
#    form_fields = ('name',)

#######################

