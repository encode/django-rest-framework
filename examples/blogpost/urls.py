from django.conf.urls.defaults import patterns, url
from djangorestframework.views import ListOrCreateModelView, InstanceModelView
from blogpost.resources import BlogPostResource, CommentResource


urlpatterns = patterns('',
    url(r'^$', ListOrCreateModelView.as_view(resource=BlogPostResource), name='blog-posts-root'),
    url(r'^(?P<key>[^/]+)/$', InstanceModelView.as_view(resource=BlogPostResource), name='blog-post'),
    url(r'^(?P<blogpost>[^/]+)/comments/$', ListOrCreateModelView.as_view(resource=CommentResource), name='comments'),
    url(r'^(?P<blogpost>[^/]+)/comments/(?P<id>[^/]+)/$', InstanceModelView.as_view(resource=CommentResource)),
)
