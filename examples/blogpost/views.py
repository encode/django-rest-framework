from flywheel.response import Response, status
from flywheel.resource import Resource
from flywheel.modelresource import ModelResource, QueryModelResource
from blogpost.models import BlogPost, Comment

##### Root Resource #####

class RootResource(Resource):
    """This is the top level resource for the API.
    All the sub-resources are discoverable from here."""
    allowed_methods = ('GET',)

    def get(self, request, *args, **kwargs):
        return Response(status.HTTP_200_OK,
                        {'blog-posts': self.reverse(BlogPostList),
                         'blog-post': self.reverse(BlogPostCreator)})


##### Blog Post Resources #####

BLOG_POST_FIELDS = ('created', 'title', 'slug', 'content', 'absolute_url', 'comment_url', 'comments_url')

class BlogPostList(QueryModelResource):
    """A resource which lists all existing blog posts."""
    allowed_methods = ('GET', )
    model = BlogPost
    fields = BLOG_POST_FIELDS

class BlogPostCreator(ModelResource):
    """A resource with which blog posts may be created."""
    allowed_methods = ('POST',)
    model = BlogPost
    fields = BLOG_POST_FIELDS

class BlogPostInstance(ModelResource):
    """A resource which represents a single blog post."""
    allowed_methods = ('GET', 'PUT', 'DELETE')
    model = BlogPost
    fields = BLOG_POST_FIELDS


##### Comment Resources #####

COMMENT_FIELDS = ('username', 'comment', 'created', 'rating', 'absolute_url', 'blogpost_url')

class CommentList(QueryModelResource):
    """A resource which lists all existing comments for a given blog post."""
    allowed_methods = ('GET', )
    model = Comment
    fields = COMMENT_FIELDS

class CommentCreator(ModelResource):
    """A resource with which blog comments may be created for a given blog post."""
    allowed_methods = ('POST',)
    model = Comment
    fields = COMMENT_FIELDS

class CommentInstance(ModelResource):
    """A resource which represents a single comment."""
    allowed_methods = ('GET', 'PUT', 'DELETE')
    model = Comment
    fields = COMMENT_FIELDS

