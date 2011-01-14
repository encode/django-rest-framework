from rest.resource import Resource
from rest.modelresource import ModelResource, QueryModelResource
from testapp.models import BlogPost, Comment

##### Root Resource #####

class RootResource(Resource):
    """This is the top level resource for the API.
    All the sub-resources are discoverable from here."""
    allowed_operations = ('read',)

    def read(self, headers={}, *args, **kwargs):
        return (200, {'blog-posts': self.reverse(BlogPostList),
                      'blog-post': self.reverse(BlogPostCreator)}, {})


##### Blog Post Resources #####

BLOG_POST_FIELDS = ('created', 'title', 'slug', 'content', 'absolute_url', 'comment_url', 'comments_url')

class BlogPostList(QueryModelResource):
    """A resource which lists all existing blog posts."""
    allowed_operations = ('read', )
    model = BlogPost
    fields = BLOG_POST_FIELDS

class BlogPostCreator(ModelResource):
    """A resource with which blog posts may be created."""
    allowed_operations = ('create',)
    model = BlogPost
    fields = BLOG_POST_FIELDS

class BlogPostInstance(ModelResource):
    """A resource which represents a single blog post."""
    allowed_operations = ('read', 'update', 'delete')
    model = BlogPost
    fields = BLOG_POST_FIELDS


##### Comment Resources #####

COMMENT_FIELDS = ('username', 'comment', 'created', 'rating', 'absolute_url', 'blogpost_url')

class CommentList(QueryModelResource):
    """A resource which lists all existing comments for a given blog post."""
    allowed_operations = ('read', )
    model = Comment
    fields = COMMENT_FIELDS

class CommentCreator(ModelResource):
    """A resource with which blog comments may be created for a given blog post."""
    allowed_operations = ('create',)
    model = Comment
    fields = COMMENT_FIELDS

class CommentInstance(ModelResource):
    """A resource which represents a single comment."""
    allowed_operations = ('read', 'update', 'delete')
    model = Comment
    fields = COMMENT_FIELDS
  

  
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

