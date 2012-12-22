<iframe src="http://ghbtns.com/github-btn.html?user=tomchristie&amp;repo=django-rest-framework&amp;type=watch&amp;count=true" allowtransparency="true" frameborder="0" scrolling="0" width="110px" height="20px"></iframe>
[![Travis build image][travis-build-image]][travis]

# Django REST framework

**A toolkit for building well-connected, self-describing Web APIs.**

---

**Note**: This documentation is for the 2.0 version of REST framework.  If you are looking for earlier versions please see the [0.4.x branch][0.4] on GitHub.

---

Django REST framework is a lightweight library that makes it easy to build Web APIs.  It is designed as a modular and easy to customize architecture, based on Django's class based views.

Web APIs built using REST framework are fully self-describing and web browseable - a huge useability win for your developers.  It also supports a wide range of media types, authentication and permission policies out of the box.

If you are considering using REST framework for your API, we recommend reading the [REST framework 2 announcment][rest-framework-2-announcement] which gives a good overview of the framework and it's capabilities.

There is also a sandbox API you can use for testing purposes, [available here][sandbox].

**Below**: *Screenshot from the browseable API*

![Screenshot][image]

## Requirements

REST framework requires the following:

* Python (2.6, 2.7)
* Django (1.3, 1.4, 1.5)

The following packages are optional:

* [Markdown][markdown] (2.1.0+) - Markdown support for the browseable API.
* [PyYAML][yaml] (3.10+) - YAML content-type support.
* [django-filter][django-filter] (0.5.4+) - Filtering support.

## Installation

Install using `pip`, including any optional packages you want...

    pip install djangorestframework
    pip install markdown  # Markdown support for the browseable API.
    pip install pyyaml    # YAML content-type support.
    pip install django-filter  # Filtering support

...or clone the project from github.

    git clone git@github.com:tomchristie/django-rest-framework.git
    cd django-rest-framework
    pip install -r requirements.txt
    pip install -r optionals.txt

Add `rest_framework` to your `INSTALLED_APPS`.

    INSTALLED_APPS = (
        ...
        'rest_framework',        
    )

If you're intending to use the browseable API you'll want to add REST framework's login and logout views.  Add the following to your root `urls.py` file.

    urlpatterns = patterns('',
        ...
        url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
    )

Note that the URL path can be whatever you want, but you must include `rest_framework.urls` with the `rest_framework` namespace.

## Quickstart

Can't wait to get started?  The [quickstart guide][quickstart] is the fastest way to get up and running with REST framework.

## Tutorial

The tutorial will walk you through the building blocks that make up REST framework.   It'll take a little while to get through, but it'll give you a comprehensive understanding of how everything fits together, and is highly recommended reading.

* [1 - Serialization][tut-1]
* [2 - Requests & Responses][tut-2]
* [3 - Class based views][tut-3]
* [4 - Authentication & permissions][tut-4]
* [5 - Relationships & hyperlinked APIs][tut-5]

## API Guide

The API guide is your complete reference manual to all the functionality provided by REST framework.

* [Requests][request]
* [Responses][response]
* [Views][views]
* [Generic views][generic-views]
* [Parsers][parsers]
* [Renderers][renderers]
* [Serializers][serializers]
* [Serializer fields][fields]
* [Authentication][authentication]
* [Permissions][permissions]
* [Throttling][throttling]
* [Filtering][filtering]
* [Pagination][pagination]
* [Content negotiation][contentnegotiation]
* [Format suffixes][formatsuffixes]
* [Returning URLs][reverse]
* [Exceptions][exceptions]
* [Status codes][status]
* [Settings][settings]

## Topics

General guides to using REST framework.

* [Browser enhancements][browser-enhancements]
* [The Browsable API][browsableapi]
* [REST, Hypermedia & HATEOAS][rest-hypermedia-hateoas]
* [2.0 Announcement][rest-framework-2-announcement]
* [Release Notes][release-notes]
* [Credits][credits]

## Development

If you want to work on REST framework itself, clone the repository, then...

Build the docs:

    ./mkdocs.py

Run the tests:

    ./rest_framework/runtests/runtests.py

## Support

For support please see the [REST framework discussion group][group], or try the  `#restframework` channel on `irc.freenode.net`.

Paid support is also available from [DabApps], and can include work on REST framework core, or support with building your REST framework API.  Please contact [Tom Christie][email] if you'd like to discuss commercial support options.

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

[travis]: http://travis-ci.org/tomchristie/django-rest-framework?branch=master
[travis-build-image]: https://secure.travis-ci.org/tomchristie/django-rest-framework.png?branch=restframework2
[urlobject]: https://github.com/zacharyvoase/urlobject
[markdown]: http://pypi.python.org/pypi/Markdown/
[yaml]: http://pypi.python.org/pypi/PyYAML
[django-filter]: https://github.com/alex/django-filter
[0.4]: https://github.com/tomchristie/django-rest-framework/tree/0.4.X
[image]: img/quickstart.png
[sandbox]: http://restframework.herokuapp.com/

[quickstart]: tutorial/quickstart.md
[tut-1]: tutorial/1-serialization.md
[tut-2]: tutorial/2-requests-and-responses.md
[tut-3]: tutorial/3-class-based-views.md
[tut-4]: tutorial/4-authentication-and-permissions.md
[tut-5]: tutorial/5-relationships-and-hyperlinked-apis.md

[request]: api-guide/requests.md
[response]: api-guide/responses.md
[views]: api-guide/views.md
[generic-views]: api-guide/generic-views.md
[parsers]: api-guide/parsers.md
[renderers]: api-guide/renderers.md
[serializers]: api-guide/serializers.md
[fields]: api-guide/fields.md
[authentication]: api-guide/authentication.md
[permissions]: api-guide/permissions.md
[throttling]: api-guide/throttling.md
[filtering]: api-guide/filtering.md
[pagination]: api-guide/pagination.md
[contentnegotiation]: api-guide/content-negotiation.md
[formatsuffixes]: api-guide/format-suffixes.md
[reverse]: api-guide/reverse.md
[exceptions]: api-guide/exceptions.md
[status]: api-guide/status-codes.md
[settings]: api-guide/settings.md

[csrf]: topics/csrf.md
[browser-enhancements]: topics/browser-enhancements.md
[browsableapi]: topics/browsable-api.md
[rest-hypermedia-hateoas]: topics/rest-hypermedia-hateoas.md
[contributing]: topics/contributing.md
[rest-framework-2-announcement]: topics/rest-framework-2-announcement.md
[release-notes]: topics/release-notes.md
[credits]: topics/credits.md

[group]: https://groups.google.com/forum/?fromgroups#!forum/django-rest-framework
[DabApps]: http://dabapps.com
[email]: mailto:tom@tomchristie.com
