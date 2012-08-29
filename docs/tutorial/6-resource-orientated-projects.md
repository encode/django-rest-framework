serializers.py

    class BlogPostSerializer(URLModelSerializer):
        class Meta:
            model = BlogPost

    class CommentSerializer(URLModelSerializer):
        class Meta:
            model = Comment

resources.py

    class BlogPostResource(ModelResource):
        serializer_class = BlogPostSerializer
        model = BlogPost
        permissions = [AdminOrAnonReadonly()]
        throttles = [AnonThrottle(rate='5/min')]

    class CommentResource(ModelResource):
        serializer_class = CommentSerializer
        model = Comment
        permissions = [AdminOrAnonReadonly()]
        throttles = [AnonThrottle(rate='5/min')]

Now that we're using Resources rather than Views, we don't need to design the urlconf ourselves.  The conventions for wiring up resources into views and urls are handled automatically.  All we need to do is register the appropriate resources with a router, and let it do the rest.  Here's our re-wired `urls.py` file.

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
* Follow me on Twitter and say hi.

Now go build something great.