from djangorestframework.response import Response, status
from djangorestframework.resource import Resource
from djangorestframework.modelresource import ModelResource, RootModelResource
from blogpost.models import BlogPost, Comment

BLOG_POST_FIELDS = ('created', 'title', 'slug', 'content', 'absolute_url', 'comment_url', 'comments_url')
COMMENT_FIELDS = ('username', 'comment', 'created', 'rating', 'absolute_url', 'blogpost_url')


class BlogPostRoot(RootModelResource):
    """A resource with which lists all existing blog posts and creates new blog posts."""
    allowed_methods = ('GET', 'POST',)
    model = BlogPost
    fields = BLOG_POST_FIELDS

class BlogPostInstance(ModelResource):
    """A resource which represents a single blog post."""
    allowed_methods = ('GET', 'PUT', 'DELETE')
    model = BlogPost
    fields = BLOG_POST_FIELDS

class CommentRoot(RootModelResource):
    """A resource which lists all existing comments for a given blog post, and creates new blog comments for a given blog post."""
    allowed_methods = ('GET', 'POST',)
    model = Comment
    fields = COMMENT_FIELDS

class CommentInstance(ModelResource):
    """A resource which represents a single comment."""
    allowed_methods = ('GET', 'PUT', 'DELETE')
    model = Comment
    fields = COMMENT_FIELDS

