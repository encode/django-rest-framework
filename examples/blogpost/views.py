from djangorestframework.response import Response
from djangorestframework.resource import Resource
from djangorestframework.modelresource import ModelResource, RootModelResource
from djangorestframework import status

from blogpost import models

BLOG_POST_FIELDS = ('created', 'title', 'slug', 'content', 'absolute_url', 'comment_url', 'comments_url')
COMMENT_FIELDS = ('username', 'comment', 'created', 'rating', 'absolute_url', 'blogpost_url')


class BlogPosts(RootModelResource):
    """A resource with which lists all existing blog posts and creates new blog posts."""
    anon_allowed_methods = allowed_methods = ('GET', 'POST',)
    model = models.BlogPost
    fields = BLOG_POST_FIELDS

class BlogPostInstance(ModelResource):
    """A resource which represents a single blog post."""
    anon_allowed_methods = allowed_methods = ('GET', 'PUT', 'DELETE')
    model = models.BlogPost
    fields = BLOG_POST_FIELDS

class Comments(RootModelResource):
    """A resource which lists all existing comments for a given blog post, and creates new blog comments for a given blog post."""
    anon_allowed_methods = allowed_methods = ('GET', 'POST',)
    model = models.Comment
    fields = COMMENT_FIELDS

class CommentInstance(ModelResource):
    """A resource which represents a single comment."""
    anon_allowed_methods = allowed_methods = ('GET', 'PUT', 'DELETE')
    model = models.Comment
    fields = COMMENT_FIELDS

