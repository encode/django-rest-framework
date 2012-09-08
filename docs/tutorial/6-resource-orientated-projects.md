## Registering Resources

resources.py

    from djangorestframework.routers import DefaultResourceRouter
    from models import BlogPost

    class BlogPostResource (ModelResource):
        pass

    class CommentResource (ModelResource):
        pass

    api = DefaultResourceRouter()
    api.register(BlogPost, BlogPostResource)
    api.register(Comment, CommentResource)

urls.py

    from resources import router

    urlpatterns = api.urlpatterns

### Do you need a resource at all?

In the preceding example, the `Resource` classes don't define any custom values
(yet). As a result, the default model resource will be provided. If you are
happy with the default resource, you don't need to define a `Resource`
object at all -- you can register the resource without providing a `Resource`
description. The preceding example could be simplified to:

    from djangorestframework.routers import DefaultResourceRouter
    from models import BlogPost

    router = DefaultResourceRouter()
    router.register(BlogPost)
    router.register(CommentPost)

## ModelResource options

*ModelResource.serializer_class*

Defaults to `ModelSerializer`.

*ModelResource.permissions*

Defaults to `DEFAULT_PERMISSIONS`.

*ModelResource.throttles*

Defaults to `DEFAULT_THROTTLES`.

*ModelResource.list_view_class*

Defaults to `RootAPIView`.  Set to `ListAPIView` for read-only.

*ModelResource.instance_view_class*

Defaults to `InstanceAPIView`.  Set to `DetailAPIView` for read-only.

*ModelResource.collection_name*

If `None`, the model's `verbose_name_plural` will be used.

*ModelResource.id_field_name*

Defaults to `'pk'`.

## Trade-offs between views vs resources.

Writing resource-orientated code can be a good thing.  It helps ensure that URL conventions will be consistent across your APIs, and minimises the amount of code you need to write.

The trade-off is that the behaviour is less explict.  It can be more difficult to determine what code path is being followed, or where to override some behaviour.

## Onwards and upwards.

We've reached the end of our tutorial.  If you want to get more involved in the REST framework project, here's a few places you can start:

* Contribute on GitHub by reviewing issues, and submitting issues or pull requests.
* Join the REST framework group, and help build the community.
* Follow me [on Twitter](https://twitter.com/_tomchristie) and say hi.

Now go build something great.
