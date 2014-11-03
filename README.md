# Django REST framework

[![build-status-image]][travis]

**Awesome web-browseable Web APIs.**

Full documentation for the project is available at [http://www.django-rest-framework.org][docs].

---

**Note**: The incoming 3.0 version has now been merged to the `master` branch on GitHub. For the source of the currently available PyPI version, please see the `2.4.4` tag.

---

# Overview

Django REST framework is a powerful and flexible toolkit for building Web APIs.

Some reasons you might want to use REST framework:

* The [Web browseable API][sandbox] is a huge useability win for your developers.
* [Authentication policies][authentication] including [OAuth1a][oauth1-section] and [OAuth2][oauth2-section] out of the box.
* [Serialization][serializers] that supports both [ORM][modelserializer-section] and [non-ORM][serializer-section] data sources.
* Customizable all the way down - just use [regular function-based views][functionview-section] if you don't need the [more][generic-views] [powerful][viewsets] [features][routers].
* [Extensive documentation][index], and [great community support][group].

There is a live example API for testing purposes, [available here][sandbox].

**Below**: *Screenshot from the browseable API*

![Screenshot][image]

# Requirements

* Python (2.6.5+, 2.7, 3.2, 3.3, 3.4)
* Django (1.4.11+, 1.5.5+, 1.6, 1.7)

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
    ./manage.py syncdb

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
# Additionally, we include login URLs for the browseable API.
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

If you believe you’ve found something in Django REST framework which has security implications, please **do not raise the issue in a public forum**.

Send a description of the issue via email to [rest-framework-security@googlegroups.com][security-mail].  The project maintainers will then work with you to resolve any issues where required, prior to any public disclosure.

# License

Copyright (c) 2011-2014, Tom Christie
All rights reserved.

Redistribution and use in source and binary forms, with or without 
modification, are permitted provided that the following conditions are met:

Redistributions of source code must retain the above copyright notice, this 
list of conditions and the following disclaimer.
Redistributions in binary form must reproduce the above copyright notice, this 
list of conditions and the following disclaimer in the documentation and/or 
other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND 
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED 
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE 
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE 
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL 
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER 
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, 
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE 
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


[build-status-image]: https://secure.travis-ci.org/tomchristie/django-rest-framework.png?branch=master
[travis]: http://travis-ci.org/tomchristie/django-rest-framework?branch=master
[twitter]: https://twitter.com/_tomchristie
[group]: https://groups.google.com/forum/?fromgroups#!forum/django-rest-framework
[0.4]: https://github.com/tomchristie/django-rest-framework/tree/0.4.X
[sandbox]: http://restframework.herokuapp.com/

[index]: http://www.django-rest-framework.org/
[oauth1-section]: http://www.django-rest-framework.org/api-guide/authentication.html#oauthauthentication
[oauth2-section]: http://www.django-rest-framework.org/api-guide/authentication.html#oauth2authentication
[serializer-section]: http://www.django-rest-framework.org/api-guide/serializers.html#serializers
[modelserializer-section]: http://www.django-rest-framework.org/api-guide/serializers.html#modelserializer
[functionview-section]: http://www.django-rest-framework.org/api-guide/views.html#function-based-views
[generic-views]: http://www.django-rest-framework.org/api-guide/generic-views.html
[viewsets]: http://www.django-rest-framework.org/api-guide/viewsets.html
[routers]: http://www.django-rest-framework.org/api-guide/routers.html
[serializers]: http://www.django-rest-framework.org/api-guide/serializers.html
[authentication]: http://www.django-rest-framework.org/api-guide/authentication.html

[rest-framework-2-announcement]: http://www.django-rest-framework.org/topics/rest-framework-2-announcement.html
[2.1.0-notes]: https://groups.google.com/d/topic/django-rest-framework/Vv2M0CMY9bg/discussion
[image]: http://www.django-rest-framework.org/img/quickstart.png

[tox]: http://testrun.org/tox/latest/

[tehjones]: https://twitter.com/tehjones/status/294986071979196416
[wlonk]: https://twitter.com/wlonk/status/261689665952833536
[laserllama]: https://twitter.com/laserllama/status/328688333750407168

[docs]: http://www.django-rest-framework.org/
[urlobject]: https://github.com/zacharyvoase/urlobject
[markdown]: http://pypi.python.org/pypi/Markdown/
[pyyaml]: http://pypi.python.org/pypi/PyYAML
[defusedxml]: https://pypi.python.org/pypi/defusedxml
[django-filter]: http://pypi.python.org/pypi/django-filter
[security-mail]: mailto:rest-framework-security@googlegroups.com
