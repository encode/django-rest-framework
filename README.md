# [Django REST framework][docs]

[![build-status-image]][travis]
[![coverage-status-image]][codecov]
[![pypi-version]][pypi]

**Awesome web-browsable Web APIs.**

Full documentation for the project is available at [https://www.django-rest-framework.org/][docs].

---

# Funding

REST framework is a *collaboratively funded project*. If you use
REST framework commercially we strongly encourage you to invest in its
continued development by [signing up for a paid plan][funding].

The initial aim is to provide a single full-time position on REST framework.
*Every single sign-up makes a significant impact towards making that possible.*

[![][sentry-img]][sentry-url]
[![][stream-img]][stream-url]
[![][rollbar-img]][rollbar-url]
[![][esg-img]][esg-url]
[![][retool-img]][retool-url]
[![][bitio-img]][bitio-url]

Many thanks to all our [wonderful sponsors][sponsors], and in particular to our premium backers, [Sentry][sentry-url], [Stream][stream-url], [Rollbar][rollbar-url], [ESG][esg-url], [Retool][retool-url], and [bit.io][bitio-url].

---

# Overview

Django REST framework is a powerful and flexible toolkit for building Web APIs.

Some reasons you might want to use REST framework:

* The [Web browsable API][sandbox] is a huge usability win for your developers.
* [Authentication policies][authentication] including optional packages for [OAuth1a][oauth1-section] and [OAuth2][oauth2-section].
* [Serialization][serializers] that supports both [ORM][modelserializer-section] and [non-ORM][serializer-section] data sources.
* Customizable all the way down - just use [regular function-based views][functionview-section] if you don't need the [more][generic-views] [powerful][viewsets] [features][routers].
* [Extensive documentation][docs], and [great community support][group].

There is a live example API for testing purposes, [available here][sandbox].

**Below**: *Screenshot from the browsable API*

![Screenshot][image]

----

# Requirements

* Python (3.5, 3.6, 3.7, 3.8, 3.9)
* Django (2.2, 3.0, 3.1)

We **highly recommend** and only officially support the latest patch release of
each Python and Django series.

# Installation

Install using `pip`...

    pip install djangorestframework

Add `'rest_framework'` to your `INSTALLED_APPS` setting.

    INSTALLED_APPS = [
        ...
        'rest_framework',
    ]

# Example

Let's take a look at a quick example of using REST framework to build a simple model-backed API for accessing users and groups.

Startup up a new project like so...

    pip install django
    pip install djangorestframework
    django-admin startproject example .
    ./manage.py migrate
    ./manage.py createsuperuser


Now edit the `example/urls.py` module in your project:

```python
from django.urls import path, include
from django.contrib.auth.models import User
from rest_framework import serializers, viewsets, routers

# Serializers define the API representation.
class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'is_staff']


# ViewSets define the view behavior.
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


# Routers provide a way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'users', UserViewSet)


# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
```

We'd also like to configure a couple of settings for our API.

Add the following to your `settings.py` module:

```python
INSTALLED_APPS = [
    ...  # Make sure to include the default installed apps here.
    'rest_framework',
]

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ]
}
```

That's it, we're done!

    ./manage.py runserver

You can now open the API in your browser at `http://127.0.0.1:8000/`, and view your new 'users' API. If you use the `Login` control in the top right corner you'll also be able to add, create and delete users from the system.

You can also interact with the API using command line tools such as [`curl`](https://curl.haxx.se/). For example, to list the users endpoint:

    $ curl -H 'Accept: application/json; indent=4' -u admin:password http://127.0.0.1:8000/users/
    [
        {
            "url": "http://127.0.0.1:8000/users/1/",
            "username": "admin",
            "email": "admin@example.com",
            "is_staff": true,
        }
    ]

Or to create a new user:

    $ curl -X POST -d username=new -d email=new@example.com -d is_staff=false -H 'Accept: application/json; indent=4' -u admin:password http://127.0.0.1:8000/users/
    {
        "url": "http://127.0.0.1:8000/users/2/",
        "username": "new",
        "email": "new@example.com",
        "is_staff": false,
    }

# Documentation & Support

Full documentation for the project is available at [https://www.django-rest-framework.org/][docs].

For questions and support, use the [REST framework discussion group][group], or `#restframework` on freenode IRC.

You may also want to [follow the author on Twitter][twitter].

# Security

Please see the [security policy][security-policy].

[build-status-image]: https://secure.travis-ci.org/encode/django-rest-framework.svg?branch=master
[travis]: https://travis-ci.org/encode/django-rest-framework?branch=master
[coverage-status-image]: https://img.shields.io/codecov/c/github/encode/django-rest-framework/master.svg
[codecov]: https://codecov.io/github/encode/django-rest-framework?branch=master
[pypi-version]: https://img.shields.io/pypi/v/djangorestframework.svg
[pypi]: https://pypi.org/project/djangorestframework/
[twitter]: https://twitter.com/_tomchristie
[group]: https://groups.google.com/forum/?fromgroups#!forum/django-rest-framework
[sandbox]: https://restframework.herokuapp.com/

[funding]: https://fund.django-rest-framework.org/topics/funding/
[sponsors]: https://fund.django-rest-framework.org/topics/funding/#our-sponsors

[sentry-img]: https://raw.githubusercontent.com/encode/django-rest-framework/master/docs/img/premium/sentry-readme.png
[stream-img]: https://raw.githubusercontent.com/encode/django-rest-framework/master/docs/img/premium/stream-readme.png
[rollbar-img]: https://raw.githubusercontent.com/encode/django-rest-framework/master/docs/img/premium/rollbar-readme.png
[esg-img]: https://raw.githubusercontent.com/encode/django-rest-framework/master/docs/img/premium/esg-readme.png
[retool-img]: https://raw.githubusercontent.com/encode/django-rest-framework/master/docs/img/premium/retool-readme.png
[bitio-img]: https://raw.githubusercontent.com/encode/django-rest-framework/master/docs/img/premium/bitio-readme.png

[sentry-url]: https://getsentry.com/welcome/
[stream-url]: https://getstream.io/try-the-api/?utm_source=drf&utm_medium=banner&utm_campaign=drf
[rollbar-url]: https://rollbar.com/?utm_source=django&utm_medium=sponsorship&utm_campaign=freetrial
[esg-url]: https://software.esg-usa.com/
[retool-url]: https://retool.com/?utm_source=djangorest&utm_medium=sponsorship
[bitio-url]: https://bit.io/jobs?utm_source=DRF&utm_medium=sponsor&utm_campaign=DRF_sponsorship

[oauth1-section]: https://www.django-rest-framework.org/api-guide/authentication/#django-rest-framework-oauth
[oauth2-section]: https://www.django-rest-framework.org/api-guide/authentication/#django-oauth-toolkit
[serializer-section]: https://www.django-rest-framework.org/api-guide/serializers/#serializers
[modelserializer-section]: https://www.django-rest-framework.org/api-guide/serializers/#modelserializer
[functionview-section]: https://www.django-rest-framework.org/api-guide/views/#function-based-views
[generic-views]: https://www.django-rest-framework.org/api-guide/generic-views/
[viewsets]: https://www.django-rest-framework.org/api-guide/viewsets/
[routers]: https://www.django-rest-framework.org/api-guide/routers/
[serializers]: https://www.django-rest-framework.org/api-guide/serializers/
[authentication]: https://www.django-rest-framework.org/api-guide/authentication/
[image]: https://www.django-rest-framework.org/img/quickstart.png

[docs]: https://www.django-rest-framework.org/
[security-policy]: https://github.com/encode/django-rest-framework/security/policy
