# Django REST framework

**A toolkit for building well-connected, self-describing web APIs.**

[![build-status-image]][travis]

---

**Full documentation for REST framework is available on [http://django-rest-framework.org][docs].**

---

# Overview

Django REST framework is a powerful and flexible toolkit that makes it easy to build Web APIs.

Web APIs built using REST framework are fully self-describing and web browseable - a huge useability win for your developers.  It also supports a wide range of media types, authentication and permission policies out of the box.

If you are considering using REST framework for your API, we recommend reading the [REST framework 2 announcment][rest-framework-2-announcement] which gives a good overview of the framework and it's capabilities.

There is also a sandbox API you can use for testing purposes, [available here][sandbox].

**Below**: *Screenshot from the browseable API*

![Screenshot][image]

# Requirements

* Python (2.6.5+, 2.7, 3.2, 3.3)
* Django (1.3, 1.4, 1.5)

# Installation

Install using `pip`...

    pip install djangorestframework

Add `'rest_framework'` to your `INSTALLED_APPS` setting.

    INSTALLED_APPS = (
        ...
        'rest_framework',        
    )

If you're intending to use the browseable API you'll probably also want to add REST framework's login and logout views.  Add the following to your root `urls.py` file.

    urlpatterns = patterns('',
        ...
        url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
    )

Note that the URL path can be whatever you want, but you must include `'rest_framework.urls'` with the `'rest_framework'` namespace.

# Example

Let's take a look at a quick example of using REST framework to build a simple model-backed API.

We'll create a read-write API for accessing users and groups.

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
    router.register(r'users', views.UserViewSet, name='user')
    router.register(r'groups', views.GroupViewSet, name='group')


    # Wire up our API using automatic URL routing.
    # Additionally, we include login URLs for the browseable API.
    urlpatterns = patterns('',
        url(r'^', include(router.urls)),
        url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
    )

# Documentation & Support

The full documentation for the project is available at [http://django-rest-framework.org][docs].

For questions and support, use the [REST framework discussion group][group], or `#restframework` on freenode IRC.

You may also want to [follow the author on Twitter][twitter] .

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
[rest-framework-2-announcement]: http://django-rest-framework.org/topics/rest-framework-2-announcement.html
[2.1.0-notes]: https://groups.google.com/d/topic/django-rest-framework/Vv2M0CMY9bg/discussion
[image]: http://django-rest-framework.org/img/quickstart.png

[tox]: http://testrun.org/tox/latest/

[docs]: http://django-rest-framework.org/
[urlobject]: https://github.com/zacharyvoase/urlobject
[markdown]: http://pypi.python.org/pypi/Markdown/
[pyyaml]: http://pypi.python.org/pypi/PyYAML
[defusedxml]: https://pypi.python.org/pypi/defusedxml
[django-filter]: http://pypi.python.org/pypi/django-filter
