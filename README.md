# [Django REST framework][docs]

[![build-status-image]][travis]
[![coverage-status-image]][codecov]
[![pypi-version]][pypi]
[![Gitter](https://badges.gitter.im/tomchristie/django-rest-framework.svg)](https://gitter.im/tomchristie/django-rest-framework?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge)

**Awesome web-browsable Web APIs.**

Full documentation for the project is available at [http://www.django-rest-framework.org][docs].

---

# Funding

REST framework is a *collaboratively funded project*. If you use
REST framework commercially we strongly encourage you to invest in its
continued development by **[signing up for a paid plan][funding]**.

The initial aim is to provide a single full-time position on REST framework.
*Every single sign-up makes a significant impact towards making that possible.*

<p align="center">
  <a href="http://jobs.rover.com/"><img src="https://raw.githubusercontent.com/tomchristie/django-rest-framework/master/docs/img/premium/rover-readme.png"/></a>
  <a href="https://getsentry.com/welcome/"><img src="https://raw.githubusercontent.com/tomchristie/django-rest-framework/master/docs/img/premium/sentry-readme.png"/></a>
  <a href="https://getstream.io/?utm_source=drf&utm_medium=banner&utm_campaign=drf"><img src="https://raw.githubusercontent.com/tomchristie/django-rest-framework/master/docs/img/premium/stream-readme.png"/></a>
</p>

*Many thanks to all our [wonderful sponsors][sponsors], and in particular to our premium backers, [Rover](http://jobs.rover.com/), [Sentry](https://getsentry.com/welcome/), and [Stream](https://getstream.io/?utm_source=drf&utm_medium=banner&utm_campaign=drf).*

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

# Requirements

* Python (2.7, 3.2, 3.3, 3.4, 3.5)
* Django (1.8, 1.9, 1.10)

# Installation

Install using `pip`...

    pip install djangorestframework

Add `'rest_framework'` to your `INSTALLED_APPS` setting.

    INSTALLED_APPS = (
        ...
        'rest_framework',
    )

# Example

Let's take a look at a quick example of using REST framework to build a simple model-backed API for accessing users and groups.

Startup up a new project like so...

    pip install django
    pip install djangorestframework
    django-admin.py startproject example .
    ./manage.py migrate
    ./manage.py createsuperuser


Now edit the `example/urls.py` module in your project:

```python
from django.conf.urls import url, include
from django.contrib.auth.models import User
from rest_framework import serializers, viewsets, routers

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
urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
```

We'd also like to configure a couple of settings for our API.

Add the following to your `settings.py` module:

```python
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
```

That's it, we're done!

    ./manage.py runserver

You can now open the API in your browser at `http://127.0.0.1:8000/`, and view your new 'users' API. If you use the `Login` control in the top right corner you'll also be able to add, create and delete users from the system.

You can also interact with the API using command line tools such as [`curl`](http://curl.haxx.se/). For example, to list the users endpoint:

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

Full documentation for the project is available at [http://www.django-rest-framework.org][docs].

For questions and support, use the [REST framework discussion group][group], or `#restframework` on freenode IRC.

You may also want to [follow the author on Twitter][twitter].

# Security

If you believe you've found something in Django REST framework which has security implications, please **do not raise the issue in a public forum**.

Send a description of the issue via email to [rest-framework-security@googlegroups.com][security-mail].  The project maintainers will then work with you to resolve any issues where required, prior to any public disclosure.

[build-status-image]: https://secure.travis-ci.org/tomchristie/django-rest-framework.svg?branch=master
[travis]: http://travis-ci.org/tomchristie/django-rest-framework?branch=master
[coverage-status-image]: https://img.shields.io/codecov/c/github/tomchristie/django-rest-framework/master.svg
[codecov]: http://codecov.io/github/tomchristie/django-rest-framework?branch=master
[pypi-version]: https://img.shields.io/pypi/v/djangorestframework.svg
[pypi]: https://pypi.python.org/pypi/djangorestframework
[twitter]: https://twitter.com/_tomchristie
[group]: https://groups.google.com/forum/?fromgroups#!forum/django-rest-framework
[sandbox]: http://restframework.herokuapp.com/

[funding]: https://fund.django-rest-framework.org/topics/funding/
[sponsors]: https://fund.django-rest-framework.org/topics/funding/#our-sponsors

[oauth1-section]: http://www.django-rest-framework.org/api-guide/authentication/#django-rest-framework-oauth
[oauth2-section]: http://www.django-rest-framework.org/api-guide/authentication/#django-oauth-toolkit
[serializer-section]: http://www.django-rest-framework.org/api-guide/serializers/#serializers
[modelserializer-section]: http://www.django-rest-framework.org/api-guide/serializers/#modelserializer
[functionview-section]: http://www.django-rest-framework.org/api-guide/views/#function-based-views
[generic-views]: http://www.django-rest-framework.org/api-guide/generic-views/
[viewsets]: http://www.django-rest-framework.org/api-guide/viewsets/
[routers]: http://www.django-rest-framework.org/api-guide/routers/
[serializers]: http://www.django-rest-framework.org/api-guide/serializers/
[authentication]: http://www.django-rest-framework.org/api-guide/authentication/
[image]: http://www.django-rest-framework.org/img/quickstart.png

[docs]: http://www.django-rest-framework.org/
[security-mail]: mailto:rest-framework-security@googlegroups.com
