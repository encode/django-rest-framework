# Caching

> A certain woman had a very sharp consciousness but almost no
> memory ... She remembered enough to work, and she worked hard.
> - Lydia Davis

Caching in REST Framework works well with the cache utilities
provided in Django.

---

## Using cache with apiview and viewsets

Django provides a [`method_decorator`][decorator] to use
decorators with class based views. This can be used with
other cache decorators such as [`cache_page`][page],
[`vary_on_cookie`][cookie] and [`vary_on_headers`][headers].

```python
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie, vary_on_headers

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets


class UserViewSet(viewsets.ViewSet):
    # With cookie: cache requested url for each user for 2 hours
    @method_decorator(cache_page(60 * 60 * 2))
    @method_decorator(vary_on_cookie)
    def list(self, request, format=None):
        content = {
            "user_feed": request.user.get_user_feed(),
        }
        return Response(content)


class ProfileView(APIView):
    # With auth: cache requested url for each user for 2 hours
    @method_decorator(cache_page(60 * 60 * 2))
    @method_decorator(vary_on_headers("Authorization"))
    def get(self, request, format=None):
        content = {
            "user_feed": request.user.get_user_feed(),
        }
        return Response(content)


class PostView(APIView):
    # Cache page for the requested url
    @method_decorator(cache_page(60 * 60 * 2))
    def get(self, request, format=None):
        content = {
            "title": "Post title",
            "body": "Post content",
        }
        return Response(content)
```


## Using cache with @api_view decorator

When using @api_view decorator, the Django-provided method-based cache decorators such as [`cache_page`][page],
[`vary_on_cookie`][cookie] and [`vary_on_headers`][headers] can be called directly.

```python
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie

from rest_framework.decorators import api_view
from rest_framework.response import Response


@cache_page(60 * 15)
@vary_on_cookie
@api_view(["GET"])
def get_user_list(request):
    content = {"user_feed": request.user.get_user_feed()}
    return Response(content)
```


**NOTE:** The [`cache_page`][page] decorator only caches the
`GET` and `HEAD` responses with status 200.

[page]: https://docs.djangoproject.com/en/dev/topics/cache/#the-per-view-cache
[cookie]: https://docs.djangoproject.com/en/dev/topics/http/decorators/#django.views.decorators.vary.vary_on_cookie
[headers]: https://docs.djangoproject.com/en/dev/topics/http/decorators/#django.views.decorators.vary.vary_on_headers
[decorator]: https://docs.djangoproject.com/en/dev/topics/class-based-views/intro/#decorating-the-class
