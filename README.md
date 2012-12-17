# Django REST framework

**A toolkit for building well-connected, self-describing web APIs.**

**Author:** Tom Christie.  [Follow me on Twitter][twitter]

[![build-status-image]][travis]

---

**Full documentation for REST framework is available on [http://django-rest-framework.org][docs].**

Note that this is the 2.0 version of REST framework.  If you are looking for earlier versions please see the [0.4.x branch][0.4] on GitHub.

---

# Overview

Django REST framework is a lightweight library that makes it easy to build Web APIs.  It is designed as a modular and easy to customize architecture, based on Django's class based views.

Web APIs built using REST framework are fully self-describing and web browseable - a huge useability win for your developers.  It also supports a wide range of media types, authentication and permission policies out of the box.

If you are considering using REST framework for your API, we recommend reading the [REST framework 2 announcment][rest-framework-2-announcement] which gives a good overview of the framework and it's capabilities.

There is also a sandbox API you can use for testing purposes, [available here][sandbox].

# Requirements

* Python (2.6, 2.7)
* Django (1.3, 1.4, 1.5)

**Optional:**

* [Markdown] - Markdown support for the self describing API.
* [PyYAML] - YAML content type support.
* [django-filter] - Filtering support.

# Installation

Install using `pip`...

    pip install djangorestframework

...or clone the project from github.

    git clone git@github.com:tomchristie/django-rest-framework.git
    pip install -r requirements.txt

# Development

To build the docs.

    ./mkdocs.py

To run the tests.

    ./rest_framework/runtests/runtests.py

# Changelog

## 2.1.10

**Date**: 17th Dec 2012

* Bugfix: Ensure read-only fields don't have model validation applied.
* Bugfix: Fix hyperlinked fields in paginated results.

## 2.1.9

**Date**: 11th Dec 2012

* Bugfix: Fix broken nested serialization.
* Bugfix: Fix `Meta.fields` only working as tuple not as list.
* Bugfix: Edge case if unnecessarily specifying `required=False` on read only field.

## 2.1.8

**Date**: 8th Dec 2012

* Fix for creating nullable Foreign Keys with `''` as well as `None`.
* Added `null=<bool>` related field option.

## 2.1.7

**Date**: 7th Dec 2012

* Serializers now properly support nullable Foreign Keys.
* Serializer validation now includes model field validation, such as uniqueness constraints.
* Support 'true' and 'false' string values for BooleanField.
* Added pickle support for serialized data.
* Support `source='dotted.notation'` style for nested serializers.
* Make `Request.user` settable.
* Bugfix: Fix `RegexField` to work with `BrowsableAPIRenderer`

## 2.1.6

**Date**: 23rd Nov 2012

* Bugfix: Unfix DjangoModelPermissions.  (I am a doofus.)

## 2.1.5

**Date**: 23rd Nov 2012

* Bugfix: Fix DjangoModelPermissions.

## 2.1.4

**Date**: 22nd Nov 2012

* Support for partial updates with serializers.
* Added `RegexField`.
* Added `SerializerMethodField`.
* Serializer performance improvements.
* Added `obtain_token_view` to get tokens when using `TokenAuthentication`.
* Bugfix: Django 1.5 configurable user support for `TokenAuthentication`.

## 2.1.3

**Date**: 16th Nov 2012

* Added `FileField` and `ImageField`.  For use with `MultiPartParser`.
* Added `URLField` and `SlugField`.
* Support for `read_only_fields` on `ModelSerializer` classes.
* Support for clients overriding the pagination page sizes.  Use the `PAGINATE_BY_PARAM` setting or set the `paginate_by_param` attribute on a generic view.
* 201 Responses now return a 'Location' header.
* Bugfix: Serializer fields now respect `max_length`.

## 2.1.2

**Date**: 9th Nov 2012

* **Filtering support.**
* Bugfix: Support creation of objects with reverse M2M relations.

## 2.1.1

**Date**: 7th Nov 2012

* Support use of HTML exception templates.  Eg. `403.html`
* Hyperlinked fields take optional `slug_field`, `slug_url_kwarg` and `pk_url_kwarg` arguments.
* Bugfix: Deal with optional trailing slashs properly when generating breadcrumbs.
* Bugfix: Make textareas same width as other fields in browsable API.
* Private API change: `.get_serializer` now uses same `instance` and `data` ordering as serializer initialization.

## 2.1.0

**Date**: 5th Nov 2012

**Warning**: Please read [this thread][2.1.0-notes] regarding the `instance` and `data` keyword args before updating to 2.1.0.

* **Serializer `instance` and `data` keyword args have their position swapped.**
* `queryset` argument is now optional on writable model fields.
* Hyperlinked related fields optionally take `slug_field` and `slug_field_kwarg` arguments.
* Support Django's cache framework.
* Minor field improvements. (Don't stringify dicts, more robust many-pk fields.)
* Bugfixes (Support choice field in Browseable API)

## 2.0.2

**Date**: 2nd Nov 2012

* Fix issues with pk related fields in the browsable API.

## 2.0.1

**Date**: 1st Nov 2012

* Add support for relational fields in the browsable API.
* Added SlugRelatedField and ManySlugRelatedField.
* If PUT creates an instance return '201 Created', instead of '200 OK'.

## 2.0.0

**Date**: 30th Oct 2012

* Redesign of core components.
* Fix **all of the things**.

# License

Copyright (c) 2011, Tom Christie
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

[build-status-image]: https://secure.travis-ci.org/tomchristie/django-rest-framework.png?branch=restframework2
[travis]: http://travis-ci.org/tomchristie/django-rest-framework?branch=master
[twitter]: https://twitter.com/_tomchristie
[0.4]: https://github.com/tomchristie/django-rest-framework/tree/0.4.X
[sandbox]: http://restframework.herokuapp.com/
[rest-framework-2-announcement]: http://django-rest-framework.org/topics/rest-framework-2-announcement.html
[2.1.0-notes]: https://groups.google.com/d/topic/django-rest-framework/Vv2M0CMY9bg/discussion

[docs]: http://django-rest-framework.org/
[urlobject]: https://github.com/zacharyvoase/urlobject
[markdown]: http://pypi.python.org/pypi/Markdown/
[pyyaml]: http://pypi.python.org/pypi/PyYAML
[django-filter]: https://github.com/alex/django-filter

