from django.conf.urls.defaults import patterns

urlpatterns = patterns('blogpost.views',
    (r'^$', 'BlogPostRoot'),
    (r'^(?P<key>[^/]+)/$', 'BlogPostInstance'),
    (r'^(?P<blogpost_id>[^/]+)/comments/$', 'CommentRoot'),
    (r'^(?P<blogpost>[^/]+)/comments/(?P<id>[^/]+)/$', 'CommentInstance'),
)
