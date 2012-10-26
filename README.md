# Django REST framework

**A toolkit for building well-connected, self-describing web APIs.**

**Author:** Tom Christie.  [Follow me on Twitter][twitter]

[![build-status-image]][travis]

# Overview

This branch is the redesign of Django REST framework.  It is a work in progress.

For more information, check out [the documentation][docs], in particular, the tutorial is recommended as the best place to get an overview of the redesign.

# Requirements

* Python (2.6, 2.7)
* Django (1.3, 1.4, 1.5)

**Optional:**

* [Markdown] - Markdown support for the self describing API.
* [PyYAML] - YAML content type support.

# Installation

**Leaving these instructions in for the moment, they'll be valid once this becomes the master version**

Install using `pip`...

    pip install djangorestframework

...or clone the project from github.

    git clone git@github.com:tomchristie/django-rest-framework.git
    pip install -r requirements.txt

# Quickstart

**TODO**

# Development

To build the docs.

    ./mkdocs.py

To run the tests.

    ./rest_framework/runtests/runtests.py

# Changelog

## 2.0.0

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
[travis]: http://travis-ci.org/tomchristie/django-rest-framework?branch=restframework2
[twitter]: https://twitter.com/_tomchristie
[docs]: http://tomchristie.github.com/django-rest-framework/
[urlobject]: https://github.com/zacharyvoase/urlobject
[markdown]: http://pypi.python.org/pypi/Markdown/
[pyyaml]: http://pypi.python.org/pypi/PyYAML

