# Tutorial 6 - Resources

Resource classes are just View classes that don't have any handler methods bound to them.  The actions on a resource are defined, 

This allows us to:

* Encapsulate common behaviour accross a class of views, in a single Resource class.
* Seperate out the actions of a Resource from the specfics of how those actions should be bound to a particular set of URLs.

## Refactoring to use Resources, not Views

For instance, we can re-write our 4 sets of views into something more compact...

resources.py

    class BlogPostResource(ModelResource):
        serializer_class = BlogPostSerializer
        model = BlogPost
        permissions_classes = (permissions.IsAuthenticatedOrReadOnly,)
        throttle_classes = (throttles.UserRateThrottle,)

    class CommentResource(ModelResource):
        serializer_class = CommentSerializer
        model = Comment
        permissions_classes = (permissions.IsAuthenticatedOrReadOnly,)
        throttle_classes = (throttles.UserRateThrottle,)

## Binding Resources to URLs explicitly
The handler methods only get bound to the actions when we define the URLConf. Here's our urls.py:

    comment_root = CommentResource.as_view(actions={
        'get': 'list',
        'post': 'create'
    })
    comment_instance = CommentInstance.as_view(actions={
        'get': 'retrieve',
        'put': 'update',
        'delete': 'destroy'
    })
    ... # And for blog post 
    
    urlpatterns = patterns('blogpost.views',
        url(r'^$', comment_root),
        url(r'^(?P<pk>[0-9]+)$', comment_instance)
        ...  # And for blog post  
    )

## Using Routers

Right now that hasn't really saved us a lot of code.  However, now that we're using Resources rather than Views, we actually don't need to design the urlconf ourselves.  The conventions for wiring up resources into views and urls can be handled automatically, using `Router` classes.  All we need to do is register the appropriate resources with a router, and let it do the rest.  Here's our re-wired `urls.py` file.

    from blog import resources
    from djangorestframework.routers import DefaultRouter

    router = DefaultRouter()
    router.register(resources.BlogPostResource)
    router.register(resources.CommentResource)
    urlpatterns = router.urlpatterns

## Trade-offs between views vs resources.

Writing resource-orientated code can be a good thing.  It helps ensure that URL conventions will be consistent across your APIs, and minimises the amount of code you need to write.

The trade-off is that the behaviour is less explict.  It can be more difficult to determine what code path is being followed, or where to override some behaviour.

## Onwards and upwards.

We've reached the end of our tutorial.  If you want to get more involved in the REST framework project, here's a few places you can start:

* Contribute on GitHub by reviewing issues, and submitting issues or pull requests.
* Join the REST framework group, and help build the community.
* Follow me [on Twitter][twitter] and say hi.

**Now go build some awesome things.**

[twitter]: https://twitter.com/_tomchristie