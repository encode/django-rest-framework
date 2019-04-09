# Caching

> A certain woman had a very sharp conciousness but almost no
> memory ... She remembered enough to work, and she worked hard.
> - Lydia Davis

Caching in REST Framework works well with the cache utilities
provided in Django.

---

## Using cache with apiview and viewsets

Django provides a [`method_decorator`][decorator] to use
decorators with class based views. This can be used with
other cache decorators such as [`cache_page`][page] and
[`vary_on_cookie`][cookie].

```python
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets

class UserViewSet(viewsets.Viewset):

    # Cache requested url for each user for 2 hours
    @method_decorator(cache_page(60*60*2))
    @method_decorator(vary_on_cookie)
    def list(self, request, format=None):
        content = {
            'user_feed': request.user.get_user_feed()
        }
        return Response(content)

class PostView(APIView):

    # Cache page for the requested url
    @method_decorator(cache_page(60*60*2))
    def get(self, request, format=None):
        content = {
            'title': 'Post title',
            'body': 'Post content'
        }
        return Response(content)
```

**NOTE:** The [`cache_page`][page] decorator only caches the
`GET` and `HEAD` responses with status 200.

[page]: https://docs.djangoproject.com/en/dev/topics/cache/#the-per-view-cache
[cookie]: https://docs.djangoproject.com/en/dev/topics/http/decorators/#django.views.decorators.vary.vary_on_cookie
[decorator]: https://docs.djangoproject.com/en/dev/topics/class-based-views/intro/#decorating-the-class
