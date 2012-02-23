from djangorestframework.resources import ModelResource
from djangorestframework.reverse import reverse
from blogpost.models import BlogPost, Comment


class BlogPostResource(ModelResource):
    """
    A Blog Post has a *title* and *content*, and can be associated with zero or more comments.
    """
    model = BlogPost
    fields = ('created', 'title', 'slug', 'content', 'url', 'comments')
    ordering = ('-created',)

    def comments(self, instance):
        return reverse('comments', request, kwargs={'blogpost': instance.key})


class CommentResource(ModelResource):
    """
    A Comment is associated with a given Blog Post and has a *username* and *comment*, and optionally a *rating*.
    """
    model = Comment
    fields = ('username', 'comment', 'created', 'rating', 'url', 'blogpost')
    ordering = ('-created',)

    def blogpost(self, instance):
        return reverse('blog-post', request, kwargs={'key': instance.blogpost.key})
