from djangorestframework.modelresource import InstanceModelResource, RootModelResource

from blogpost import models

BLOG_POST_FIELDS = ('created', 'title', 'slug', 'content', 'absolute_url', 'comment_url', 'comments_url')
COMMENT_FIELDS = ('username', 'comment', 'created', 'rating', 'absolute_url', 'blogpost_url')
MAX_POSTS = 10

class BlogPosts(RootModelResource):
    """A resource with which lists all existing blog posts and creates new blog posts."""
    model = models.BlogPost
    fields = BLOG_POST_FIELDS

class BlogPostInstance(InstanceModelResource):
    """A resource which represents a single blog post."""
    model = models.BlogPost
    fields = BLOG_POST_FIELDS

class Comments(RootModelResource):
    """A resource which lists all existing comments for a given blog post, and creates new blog comments for a given blog post."""
    model = models.Comment
    fields = COMMENT_FIELDS

class CommentInstance(InstanceModelResource):
    """A resource which represents a single comment."""
    model = models.Comment
    fields = COMMENT_FIELDS

