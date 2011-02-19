from django.conf.urls.defaults import patterns, url
from blogpost.views import BlogPosts, BlogPostInstance, Comments, CommentInstance

urlpatterns = patterns('',
    url(r'^$', BlogPosts.as_view(), name='blog-posts'),
    url(r'^(?P<key>[^/]+)/$', BlogPostInstance.as_view(), name='blog-post'),
    url(r'^(?P<blogpost>[^/]+)/comments/$', Comments.as_view(), name='comments'),
    url(r'^(?P<blogpost>[^/]+)/comments/(?P<id>[^/]+)/$', CommentInstance.as_view(), name='comment'),
)
