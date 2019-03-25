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
[![][cadre-img]][cadre-url]
[![][kloudless-img]][kloudless-url]
[![][release-history-img]][release-history-url]
[![][lightson-img]][lightson-url]

Many thanks to all our [wonderful sponsors][sponsors], and in particular to our premium backers, [Sentry][sentry-url], [Stream][stream-url], [Rollbar][rollbar-url], [Cadre][cadre-url], [Kloudless][kloudless-url], [Release History][release-history-url], and [Lights On Software][lightson-url].

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
Funding

REST framework is a collaboratively funded project. If you use REST framework commercially we strongly encourage you to invest in its continued development by signing up for a paid plan.

The initial aim is to provide a single full-time position on REST framework. Every single sign-up makes a significant impact on making that possible.

Many thanks to all our wonderful sponsors, and in particular to our premium backers, Sentry, Stream, Rollbar, Cadre, Kloudless, Release History, and Lights On Software.
Overview

Django REST framework is a powerful and flexible toolkit for building Web APIs.

Some reasons you might want to use REST framework:

    The Web-browsable API is a huge usability win for your developers.
    Authentication policies including optional packages for OAuth1a and OAuth2.
    Serialization that supports both ORM and non-ORM data sources.
    Customizable all the way down - just use regular function-based views if you don't need the more powerful features.
    Extensive documentation, and great community support.

There is a live example API for testing purposes, available here.

Below: Screenshot from the browsable API

Screenshot
Requirements

    Python (2.7, 3.4, 3.5, 3.6, 3.7)
    Django (1.11, 2.0, 2.1, 2.2)

We highly recommend and only officially support the latest patch release of each Python and Django series.
Installation

Install using pip...

pip install djangorestframework

Add 'rest_framework' to your INSTALLED_APPS setting.

INSTALLED_APPS = (
    ...
    'rest_framework',
)

Example

Let's take a look at a quick example of using REST framework to build a simple model-backed API for accessing users and groups.

Startup up a new project like so...

pip install django
pip install djangorestframework
django-admin startproject example .
./manage.py migrate
./manage.py createsuperuser

Now edit the example/URLs.py module in your project:

from django.conf.URLs import URL, include
from django.contrib.auth.models import User
from rest_framework import serializers, view sets, routers

# Serializers define the API representation.
class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'is_staff')


# ViewSets define the view behavior.
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


# Routers provide a way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'users', UserViewSet)


# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
URL patterns = [
    url(r'^', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]

We'd also like to configure a couple of settings for our API.

Add the following to your settings.py module:

INSTALLED_APPS = (
    ...  # Make sure to include the default installed apps here.
    'rest_framework',
)

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ]
}

That's it, we're done!

./manage.py runserver

You can now open the API in your browser at http://127.0.0.1:8000/, and view your new 'users' API. If you use the Login control in the top right corner you'll also be able to add, create and delete users from the system.

You can also interact with the API using command line tools such as curl. For example, to list the user's endpoint:

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

Documentation & Support

Full documentation for the project is available at https://www.django-rest-framework.org/.

For questions and support, use the REST framework discussion group, or #restframework on Freenode IRC.

You may also want to follow the author on Twitter.
Security

If you believe you've found something in Django REST framework which has security implications, please do not raise the issue in a public forum.

Send a description of the issue via email to rest-framework-security@googlegroups.com. The project maintainers will then work with you to resolve any issues where required, prior to any public disclosure.
