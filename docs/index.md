# Django REST framework

**A toolkit for building well-connected, self-describing Web APIs.**

**WARNING: This documentation is for the 2.0 redesign of REST framework.  It is a work in progress.**

Django REST framework is a lightweight library that makes it easy to build Web APIs.  It is designed as a modular and easy to customize architecture, based on Django's class based views.

Web APIs built using REST framework are fully self-describing and web browseable - a huge useability win for your developers.  It also supports a wide range of media types, authentication and permission policies out of the box.

## Requirements

REST framework requires the following:

* Python (2.6, 2.7)
* Django (1.3, 1.4, 1.5)
* [URLObject][urlobject] (2.0.0+)

The following packages are optional:

* [Markdown][markdown] (2.1.0+) - Markdown support for the self describing API.
* [PyYAML][yaml] (3.10+) - YAML content type support.

If you're installing using `pip`, all requirements and optional packages will be installed by default.

## Installation

**WARNING: These instructions will only become valid once this becomes the master version**

Install using `pip`...

    pip install djangorestframework

...or clone the project from github.

    git clone git@github.com:tomchristie/django-rest-framework.git
    pip install -r requirements.txt

Add `djangorestframework` to your `INSTALLED_APPS`.

    INSTALLED_APPS = (
        ...
        'djangorestframework',        
    )

If you're intending to use the browserable API you'll want to add REST framework's login and logout views.  Add the following to your root `urls.py` file.

    urlpatterns = patterns('',
        ...
        url(r'^auth', include('djangorestframework.urls', namespace='djangorestframework'))
    )
 
## Quickstart

**TODO**

## Tutorial

The tutorial will walk you through the building blocks that make up REST framework.   It'll take a little while to get through, but it'll give you a comprehensive understanding of how everything fits together, and is highly recommended reading.

* [1 - Serialization][tut-1]
* [2 - Requests & Responses][tut-2]
* [3 - Class based views][tut-3]
* [4 - Authentication, permissions & throttling][tut-4]
* [5 - Relationships & hyperlinked APIs][tut-5]
* [6 - Resource orientated projects][tut-6]

## API Guide

The API guide is your complete reference manual to all the functionality provided by REST framework.

* [Requests][request]
* [Responses][response]
* [Views][views]
* [Parsers][parsers]
* [Renderers][renderers]
* [Serializers][serializers]
* [Authentication][authentication]
* [Permissions][permissions]
* [Exceptions][exceptions]
* [Status codes][status]
* [Returning URLs][urls]

## Topics

General guides to using REST framework.

* [CSRF][csrf]
* [Form overloading][formoverloading]
* [Credits][credits]

## License

Copyright (c) 2011-2012, Tom Christie
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

[urlobject]: https://github.com/zacharyvoase/urlobject
[markdown]: http://pypi.python.org/pypi/Markdown/
[yaml]: http://pypi.python.org/pypi/PyYAML

[tut-1]: tutorial/1-serialization.md
[tut-2]: tutorial/2-requests-and-responses.md
[tut-3]: tutorial/3-class-based-views.md
[tut-4]: tutorial/4-authentication-permissions-and-throttling.md
[tut-5]: tutorial/5-relationships-and-hyperlinked-apis.md
[tut-6]: tutorial/6-resource-orientated-projects.md

[request]: api-guide/requests.md
[response]: api-guide/responses.md
[views]: api-guide/views.md
[parsers]: api-guide/parsers.md
[renderers]: api-guide/renderers.md
[serializers]: api-guide/serializers.md
[authentication]: api-guide/authentication.md
[permissions]: api-guide/permissions.md
[exceptions]: api-guide/exceptions.md
[status]: api-guide/status.md
[urls]: api-guide/urls.md

[csrf]: topics/csrf.md
[formoverloading]: topics/formoverloading.md
[credits]: topics/credits.md
