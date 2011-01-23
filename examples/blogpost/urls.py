from django.conf.urls.defaults import patterns

urlpatterns = patterns('blogpost.views',
    (r'^$', 'RootResource'),   
    (r'^blog-posts/$', 'BlogPostList'),
    (r'^blog-post/$', 'BlogPostCreator'),
    (r'^blog-post/(?P<key>[^/]+)/$', 'BlogPostInstance'),
    (r'^blog-post/(?P<blogpost_id>[^/]+)/comments/$', 'CommentList'),
    (r'^blog-post/(?P<blogpost_id>[^/]+)/comment/$', 'CommentCreator'),
    (r'^blog-post/(?P<blogpost>[^/]+)/comments/(?P<id>[^/]+)/$', 'CommentInstance'),
)
