from django.conf.urls.defaults import patterns

urlpatterns = patterns('testapp.views',
    (r'^$', 'RootResource'),
    #(r'^read-only$', 'ReadOnlyResource'),
    #(r'^write-only$', 'WriteOnlyResource'),
    #(r'^read-write$', 'ReadWriteResource'),
    #(r'^model$', 'ModelFormResource'),
    #(r'^container$', 'ContainerFactory'),
    #(r'^container/((?P<key>[^/]+))$', 'ContainerInstance'),
    
    (r'^blog-posts/$', 'BlogPostList'),
    (r'^blog-post/$', 'BlogPostCreator'),
    (r'^blog-post/(?P<key>[^/]+)/$', 'BlogPostInstance'),

    (r'^blog-post/(?P<blogpost_id>[^/]+)/comments/$', 'CommentList'),
    (r'^blog-post/(?P<blogpost_id>[^/]+)/comment/$', 'CommentCreator'),
    (r'^blog-post/(?P<blogpost>[^/]+)/comments/(?P<id>[^/]+)/$', 'CommentInstance'),
)
