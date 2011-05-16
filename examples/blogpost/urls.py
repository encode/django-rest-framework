from django.conf.urls.defaults import patterns, url
from django.core.urlresolvers import reverse

from djangorestframework.views import ListOrCreateModelView, InstanceModelView
from djangorestframework.resources import ModelResource

from blogpost.models import BlogPost, Comment

class BlogPostResource(ModelResource):
    model = BlogPost
    fields = ('created', 'title', 'slug', 'content', 'url', 'comments')
    ordering = ('-created',)

    def comments(self, instance):
        return reverse('comments', kwargs={'blogpost': instance.key}) 

class CommentResource(ModelResource):
    model = Comment
    fields = ('username', 'comment', 'created', 'rating', 'url', 'blogpost')
    ordering = ('-created',)


urlpatterns = patterns('',
    url(r'^$', ListOrCreateModelView.as_view(resource=BlogPostResource), name='blog-posts-root'),
    url(r'^(?P<key>[^/]+)/$', InstanceModelView.as_view(resource=BlogPostResource)),
    url(r'^(?P<blogpost>[^/]+)/comments/$', ListOrCreateModelView.as_view(resource=CommentResource), name='comments'),
    url(r'^(?P<blogpost>[^/]+)/comments/(?P<id>[^/]+)/$', InstanceModelView.as_view(resource=CommentResource)),
)