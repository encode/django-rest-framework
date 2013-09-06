# Django REST framework

**Awesome web-browseable Web APIs.**

[![build-status-image]][travis]

**Note**: Full documentation for the project is available at [http://django-rest-framework.org][docs].

# Overview

Django REST framework is a powerful and flexible toolkit that makes it easy to build Web APIs.

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

* Python (2.6.5+, 2.7, 3.2, 3.3)
* Django (1.3, 1.4, 1.5, 1.6)

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

Here's our project's root `urls.py` module:

    from django.conf.urls.defaults import url, patterns, include
    from django.contrib.auth.models import User, Group
    from rest_framework import viewsets, routers

    # ViewSets define the view behavior.
    class UserViewSet(viewsets.ModelViewSet):
        model = User

    class GroupViewSet(viewsets.ModelViewSet):
        model = Group

    
    # Routers provide an easy way of automatically determining the URL conf
    router = routers.DefaultRouter()
    router.register(r'users', UserViewSet)
    router.register(r'groups', GroupViewSet)


    # Wire up our API using automatic URL routing.
    # Additionally, we include login URLs for the browseable API.
    urlpatterns = patterns('',
        url(r'^', include(router.urls)),
        url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
    )

We'd also like to configure a couple of settings for our API.

Add the following to your `settings.py` module:

    REST_FRAMEWORK = {
        # Use hyperlinked styles by default.
        # Only used if the `serializer_class` attribute is not set on a view.
        'DEFAULT_MODEL_SERIALIZER_CLASS':
            'rest_framework.serializers.HyperlinkedModelSerializer',

        # Use Django's standard `django.contrib.auth` permissions,
        # or allow read-only access for unauthenticated users.
        'DEFAULT_PERMISSION_CLASSES': [
            'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
        ]
    }

Don't forget to make sure you've also added `rest_framework` to your `INSTALLED_APPS` setting.

That's it, we're done!

# Documentation & Support

Full documentation for the project is available at [http://django-rest-framework.org][docs].

For questions and support, use the [REST framework discussion group][group], or `#restframework` on freenode IRC.

You may also want to [follow the author on Twitter][twitter].

# Security

If you believe you’ve found something in Django REST framework which has security implications, please **do not raise the issue in a public forum**.

Send a description of the issue via email to [rest-framework-security@googlegroups.com][security-mail].  The project maintainers will then work with you to resolve any issues where required, prior to any public disclosure.

# License

Copyright (c) 2011-2013, Tom Christie
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

[index]: http://django-rest-framework.org/
[oauth1-section]: http://django-rest-framework.org/api-guide/authentication.html#oauthauthentication
[oauth2-section]: http://django-rest-framework.org/api-guide/authentication.html#oauth2authentication
[serializer-section]: http://django-rest-framework.org/api-guide/serializers.html#serializers
[modelserializer-section]: http://django-rest-framework.org/api-guide/serializers.html#modelserializer
[functionview-section]: http://django-rest-framework.org/api-guide/views.html#function-based-views
[generic-views]: http://django-rest-framework.org/api-guide/generic-views.html
[viewsets]: http://django-rest-framework.org/api-guide/viewsets.html
[routers]: http://django-rest-framework.org/api-guide/routers.html
[serializers]: http://django-rest-framework.org/api-guide/serializers.html
[authentication]: http://django-rest-framework.org/api-guide/authentication.html

[rest-framework-2-announcement]: http://django-rest-framework.org/topics/rest-framework-2-announcement.html
[2.1.0-notes]: https://groups.google.com/d/topic/django-rest-framework/Vv2M0CMY9bg/discussion
[image]: http://django-rest-framework.org/img/quickstart.png

[tox]: http://testrun.org/tox/latest/

[tehjones]: https://twitter.com/tehjones/status/294986071979196416
[wlonk]: https://twitter.com/wlonk/status/261689665952833536
[laserllama]: https://twitter.com/laserllama/status/328688333750407168

[docs]: http://django-rest-framework.org/
[urlobject]: https://github.com/zacharyvoase/urlobject
[markdown]: http://pypi.python.org/pypi/Markdown/
[pyyaml]: http://pypi.python.org/pypi/PyYAML
[defusedxml]: https://pypi.python.org/pypi/defusedxml
[django-filter]: http://pypi.python.org/pypi/django-filter
[security-mail]: mailto:rest-framework-security@googlegroups.com
