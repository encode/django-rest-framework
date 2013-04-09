<a class="github" href="routers.py"></a>

# Routers

> Resource routing allows you to quickly declare all of the common routes for a given resourceful controller. Instead of declaring separate routes for your index... a resourceful route declares them in a single line of code.
>
> &mdash; [Ruby on Rails Documentation][cite]

Some Web frameworks such as Rails provide functionality for automatically determining how the URLs for an application should be mapped to the logic that deals with handling incoming requests.

Conversely, Django stops short of automatically generating URLs, and requires you to explicitly manage your URL configuration.

REST framework adds support for automatic URL routing, which provides you with a simple, quick and consistent way of wiring your view logic to a set of URLs.

# API Guide

Routers provide a convenient and simple shortcut for wiring up your application's URLs.

    router = routers.DefaultRouter()
    router.register('^/', APIRoot, 'api-root')
    router.register('^users/', UserViewSet, 'user')
    router.register('^groups/', GroupViewSet, 'group')
    router.register('^accounts/', AccountViewSet, 'account')

    urlpatterns = router.urlpatterns

[cite]: http://guides.rubyonrails.org/routing.html