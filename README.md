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

# File Structure tree

├── codecov.yml
├── CONTRIBUTING.md
├── docs
│   ├── api-guide
│   │   ├── authentication.md
│   │   ├── caching.md
│   │   ├── content-negotiation.md
│   │   ├── exceptions.md
│   │   ├── fields.md
│   │   ├── filtering.md
│   │   ├── format-suffixes.md
│   │   ├── generic-views.md
│   │   ├── metadata.md
│   │   ├── pagination.md
│   │   ├── parsers.md
│   │   ├── permissions.md
│   │   ├── relations.md
│   │   ├── renderers.md
│   │   ├── requests.md
│   │   ├── responses.md
│   │   ├── reverse.md
│   │   ├── routers.md
│   │   ├── schemas.md
│   │   ├── serializers.md
│   │   ├── settings.md
│   │   ├── status-codes.md
│   │   ├── testing.md
│   │   ├── throttling.md
│   │   ├── validators.md
│   │   ├── versioning.md
│   │   ├── viewsets.md
│   │   └── views.md
│   ├── CNAME
│   ├── community
│   │   ├── 3.0-announcement.md
│   │   ├── 3.10-announcement.md
│   │   ├── 3.11-announcement.md
│   │   ├── 3.12-announcement.md
│   │   ├── 3.1-announcement.md
│   │   ├── 3.2-announcement.md
│   │   ├── 3.3-announcement.md
│   │   ├── 3.4-announcement.md
│   │   ├── 3.5-announcement.md
│   │   ├── 3.6-announcement.md
│   │   ├── 3.7-announcement.md
│   │   ├── 3.8-announcement.md
│   │   ├── 3.9-announcement.md
│   │   ├── contributing.md
│   │   ├── funding.md
│   │   ├── jobs.md
│   │   ├── kickstarter-announcement.md
│   │   ├── mozilla-grant.md
│   │   ├── project-management.md
│   │   ├── release-notes.md
│   │   ├── third-party-packages.md
│   │   └── tutorials-and-resources.md
│   ├── coreapi
│   │   ├── 7-schemas-and-client-libraries.md
│   │   ├── from-documenting-your-api.md
│   │   ├── index.md
│   │   └── schemas.md
│   ├── img
│   │   ├── admin.png
│   │   ├── api-docs.gif
│   │   ├── api-docs.png
│   │   ├── bayer.png
│   │   ├── books
│   │   │   ├── bda-cover.png
│   │   │   ├── dfa-cover.jpg
│   │   │   ├── hwa-cover.png
│   │   │   └── tsd-cover.png
│   │   ├── cerulean.png
│   │   ├── corejson-format.png
│   │   ├── cursor-pagination.png
│   │   ├── drf-yasg.png
│   │   ├── filter-controls.png
│   │   ├── horizontal.png
│   │   ├── inline.png
│   │   ├── labels-and-milestones.png
│   │   ├── link-header-pagination.png
│   │   ├── logo.png
│   │   ├── ordering-filter.png
│   │   ├── pages-pagination.png
│   │   ├── premium
│   │   │   ├── bitio-readme.png
│   │   │   ├── cadre-readme.png
│   │   │   ├── esg-readme.png
│   │   │   ├── kloudless-readme.png
│   │   │   ├── lightson-readme.png
│   │   │   ├── release-history.png
│   │   │   ├── retool-readme.png
│   │   │   ├── rollbar-readme.png
│   │   │   ├── sentry-readme.png
│   │   │   └── stream-readme.png
│   │   ├── quickstart.png
│   │   ├── raml.png
│   │   ├── rover.png
│   │   ├── search-filter.png
│   │   ├── self-describing.png
│   │   ├── slate.png
│   │   ├── sponsors
│   │   │   ├── 0-eventbrite.png
│   │   │   ├── 1-cyan.png
│   │   │   ├── 1-divio.png
│   │   │   ├── 1-kuwaitnet.png
│   │   │   ├── 1-lulu.png
│   │   │   ├── 1-potato.png
│   │   │   ├── 1-purplebit.png
│   │   │   ├── 1-runscope.png
│   │   │   ├── 1-simple-energy.png
│   │   │   ├── 1-vokal_interactive.png
│   │   │   ├── 1-wiredrive.png
│   │   │   ├── 2-byte.png
│   │   │   ├── 2-compile.png
│   │   │   ├── 2-crate.png
│   │   │   ├── 2-cryptico.png
│   │   │   ├── 2-django.png
│   │   │   ├── 2-heroku.png
│   │   │   ├── 2-hipflask.png
│   │   │   ├── 2-hipo.png
│   │   │   ├── 2-koordinates.png
│   │   │   ├── 2-laterpay.png
│   │   │   ├── 2-lightning_kite.png
│   │   │   ├── 2-mirus_research.png
│   │   │   ├── 2-nexthub.png
│   │   │   ├── 2-opbeat.png
│   │   │   ├── 2-prorenata.png
│   │   │   ├── 2-pulsecode.png
│   │   │   ├── 2-rapasso.png
│   │   │   ├── 2-rheinwerk_verlag.png
│   │   │   ├── 2-schuberg_philis.png
│   │   │   ├── 2-security_compass.png
│   │   │   ├── 2-sga.png
│   │   │   ├── 2-singing-horse.png
│   │   │   ├── 2-sirono.png
│   │   │   ├── 2-vinta.png
│   │   │   ├── 2-wusawork.png
│   │   │   ├── 3-aba.png
│   │   │   ├── 3-aditium.png
│   │   │   ├── 3-alwaysdata.png
│   │   │   ├── 3-ax_semantics.png
│   │   │   ├── 3-beefarm.png
│   │   │   ├── 3-blimp.png
│   │   │   ├── 3-brightloop.png
│   │   │   ├── 3-cantemo.gif
│   │   │   ├── 3-crosswordtracker.png
│   │   │   ├── 3-fluxility.png
│   │   │   ├── 3-garfo.png
│   │   │   ├── 3-gizmag.png
│   │   │   ├── 3-holvi.png
│   │   │   ├── 3-imt_computer_services.png
│   │   │   ├── 3-infinite_code.png
│   │   │   ├── 3-ipushpull.png
│   │   │   ├── 3-isl.png
│   │   │   ├── 3-life_the_game.png
│   │   │   ├── 3-makespace.png
│   │   │   ├── 3-nephila.png
│   │   │   ├── 3-openeye.png
│   │   │   ├── 3-pathwright.png
│   │   │   ├── 3-phurba.png
│   │   │   ├── 3-pkgfarm.png
│   │   │   ├── 3-providenz.png
│   │   │   ├── 3-safari.png
│   │   │   ├── 3-shippo.png
│   │   │   ├── 3-teonite.png
│   │   │   ├── 3-thermondo-gmbh.png
│   │   │   ├── 3-tivix.png
│   │   │   ├── 3-trackmaven.png
│   │   │   ├── 3-transcode.png
│   │   │   ├── 3-triggered_messaging.png
│   │   │   ├── 3-vzzual.png
│   │   │   └── 3-wildfish.png
│   │   ├── travis-status.png
│   │   └── vertical.png
│   ├── index.md
│   ├── topics
│   │   ├── ajax-csrf-cors.md
│   │   ├── api-clients.md
│   │   ├── browsable-api.md
│   │   ├── browser-enhancements.md
│   │   ├── documenting-your-api.md
│   │   ├── html-and-forms.md
│   │   ├── internationalization.md
│   │   ├── rest-hypermedia-hateoas.md
│   │   └── writable-nested-serializers.md
│   └── tutorial
│       ├── 1-serialization.md
│       ├── 2-requests-and-responses.md
│       ├── 3-class-based-views.md
│       ├── 4-authentication-and-permissions.md
│       ├── 5-relationships-and-hyperlinked-apis.md
│       ├── 6-viewsets-and-routers.md
│       └── quickstart.md
├── docs_theme
│   ├── 404.html
│   ├── css
│   │   ├── bootstrap.css
│   │   ├── bootstrap-responsive.css
│   │   ├── default.css
│   │   └── prettify.css
│   ├── img
│   │   ├── favicon.ico
│   │   ├── glyphicons-halflings.png
│   │   ├── glyphicons-halflings-white.png
│   │   └── grid.png
│   ├── js
│   │   ├── bootstrap-2.1.1-min.js
│   │   ├── jquery-1.8.1-min.js
│   │   ├── prettify-1.0.js
│   │   └── theme.js
│   ├── main.html
│   └── nav.html
├── ISSUE_TEMPLATE.md
├── LICENSE.md
├── licenses
│   ├── bootstrap.md
│   └── jquery.json-view.md
├── MANIFEST.in
├── mkdocs.yml
├── PULL_REQUEST_TEMPLATE.md
├── README.md
├── requirements
│   ├── requirements-codestyle.txt
│   ├── requirements-documentation.txt
│   ├── requirements-optionals.txt
│   ├── requirements-packaging.txt
│   └── requirements-testing.txt
├── requirements.txt
├── rest_framework
│   ├── apps.py
│   ├── authentication.py
│   ├── authtoken
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── __init__.py
│   │   ├── management
│   │   │   ├── commands
│   │   │   │   ├── drf_create_token.py
│   │   │   │   └── __init__.py
│   │   │   └── __init__.py
│   │   ├── migrations
│   │   │   ├── 0001_initial.py
│   │   │   ├── 0002_auto_20160226_1747.py
│   │   │   ├── 0003_tokenproxy.py
│   │   │   └── __init__.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   └── views.py
│   ├── checks.py
│   ├── compat.py
│   ├── decorators.py
│   ├── documentation.py
│   ├── exceptions.py
│   ├── fields.py
│   ├── filters.py
│   ├── generics.py
│   ├── __init__.py
│   ├── locale
│   │   ├── ach
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── ar
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── be
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── ca
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── ca_ES
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── cs
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── da
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── de
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── el
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── el_GR
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── en
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── en_AU
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── en_CA
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── en_US
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── es
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── et
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── fa
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── fa_IR
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── fi
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── fr
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── fr_CA
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── gl
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── gl_ES
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── he_IL
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── hu
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── id
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── it
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── ja
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── ko_KR
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── lv
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── mk
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── nb
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── nl
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── nn
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── no
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── pl
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── pt
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── pt_BR
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── pt_PT
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── ro
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── ru
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── sk
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── sl
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── sv
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── tr
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── tr_TR
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── uk
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── vi
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── zh_CN
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── zh_Hans
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   ├── zh_Hant
│   │   │   └── LC_MESSAGES
│   │   │       ├── django.mo
│   │   │       └── django.po
│   │   └── zh_TW
│   │       └── LC_MESSAGES
│   │           ├── django.mo
│   │           └── django.po
│   ├── management
│   │   ├── commands
│   │   │   ├── generateschema.py
│   │   │   └── __init__.py
│   │   └── __init__.py
│   ├── metadata.py
│   ├── mixins.py
│   ├── negotiation.py
│   ├── pagination.py
│   ├── parsers.py
│   ├── permissions.py
│   ├── relations.py
│   ├── renderers.py
│   ├── request.py
│   ├── response.py
│   ├── reverse.py
│   ├── routers.py
│   ├── schemas
│   │   ├── coreapi.py
│   │   ├── generators.py
│   │   ├── __init__.py
│   │   ├── inspectors.py
│   │   ├── openapi.py
│   │   ├── utils.py
│   │   └── views.py
│   ├── serializers.py
│   ├── settings.py
│   ├── static
│   │   └── rest_framework
│   │       ├── css
│   │       │   ├── bootstrap.min.css
│   │       │   ├── bootstrap-theme.min.css
│   │       │   ├── bootstrap-tweaks.css
│   │       │   ├── default.css
│   │       │   ├── font-awesome-4.0.3.css
│   │       │   └── prettify.css
│   │       ├── docs
│   │       │   ├── css
│   │       │   │   ├── base.css
│   │       │   │   ├── highlight.css
│   │       │   │   └── jquery.json-view.min.css
│   │       │   ├── img
│   │       │   │   ├── favicon.ico
│   │       │   │   └── grid.png
│   │       │   └── js
│   │       │       ├── api.js
│   │       │       ├── highlight.pack.js
│   │       │       └── jquery.json-view.min.js
│   │       ├── fonts
│   │       │   ├── fontawesome-webfont.eot
│   │       │   ├── fontawesome-webfont.svg
│   │       │   ├── fontawesome-webfont.ttf
│   │       │   ├── fontawesome-webfont.woff
│   │       │   ├── glyphicons-halflings-regular.eot
│   │       │   ├── glyphicons-halflings-regular.svg
│   │       │   ├── glyphicons-halflings-regular.ttf
│   │       │   ├── glyphicons-halflings-regular.woff
│   │       │   └── glyphicons-halflings-regular.woff2
│   │       ├── img
│   │       │   ├── glyphicons-halflings.png
│   │       │   ├── glyphicons-halflings-white.png
│   │       │   └── grid.png
│   │       └── js
│   │           ├── ajax-form.js
│   │           ├── bootstrap.min.js
│   │           ├── coreapi-0.1.1.js
│   │           ├── csrf.js
│   │           ├── default.js
│   │           ├── jquery-3.5.1.min.js
│   │           └── prettify-min.js
│   ├── status.py
│   ├── templates
│   │   └── rest_framework
│   │       ├── admin
│   │       │   ├── detail.html
│   │       │   ├── dict_value.html
│   │       │   ├── list.html
│   │       │   ├── list_value.html
│   │       │   └── simple_list_value.html
│   │       ├── admin.html
│   │       ├── api.html
│   │       ├── base.html
│   │       ├── docs
│   │       │   ├── auth
│   │       │   │   ├── basic.html
│   │       │   │   ├── session.html
│   │       │   │   └── token.html
│   │       │   ├── document.html
│   │       │   ├── error.html
│   │       │   ├── index.html
│   │       │   ├── interact.html
│   │       │   ├── langs
│   │       │   │   ├── javascript.html
│   │       │   │   ├── javascript-intro.html
│   │       │   │   ├── python.html
│   │       │   │   ├── python-intro.html
│   │       │   │   ├── shell.html
│   │       │   │   └── shell-intro.html
│   │       │   ├── link.html
│   │       │   └── sidebar.html
│   │       ├── filters
│   │       │   ├── base.html
│   │       │   ├── ordering.html
│   │       │   └── search.html
│   │       ├── horizontal
│   │       │   ├── checkbox.html
│   │       │   ├── checkbox_multiple.html
│   │       │   ├── dict_field.html
│   │       │   ├── fieldset.html
│   │       │   ├── form.html
│   │       │   ├── input.html
│   │       │   ├── list_field.html
│   │       │   ├── list_fieldset.html
│   │       │   ├── radio.html
│   │       │   ├── select.html
│   │       │   ├── select_multiple.html
│   │       │   └── textarea.html
│   │       ├── inline
│   │       │   ├── checkbox.html
│   │       │   ├── checkbox_multiple.html
│   │       │   ├── dict_field.html
│   │       │   ├── fieldset.html
│   │       │   ├── form.html
│   │       │   ├── input.html
│   │       │   ├── list_field.html
│   │       │   ├── list_fieldset.html
│   │       │   ├── radio.html
│   │       │   ├── select.html
│   │       │   ├── select_multiple.html
│   │       │   └── textarea.html
│   │       ├── login_base.html
│   │       ├── login.html
│   │       ├── pagination
│   │       │   ├── numbers.html
│   │       │   └── previous_and_next.html
│   │       ├── raw_data_form.html
│   │       ├── schema.js
│   │       └── vertical
│   │           ├── checkbox.html
│   │           ├── checkbox_multiple.html
│   │           ├── dict_field.html
│   │           ├── fieldset.html
│   │           ├── form.html
│   │           ├── input.html
│   │           ├── list_field.html
│   │           ├── list_fieldset.html
│   │           ├── radio.html
│   │           ├── select.html
│   │           ├── select_multiple.html
│   │           └── textarea.html
│   ├── templatetags
│   │   ├── __init__.py
│   │   └── rest_framework.py
│   ├── test.py
│   ├── throttling.py
│   ├── urlpatterns.py
│   ├── urls.py
│   ├── utils
│   │   ├── breadcrumbs.py
│   │   ├── encoders.py
│   │   ├── field_mapping.py
│   │   ├── formatting.py
│   │   ├── html.py
│   │   ├── humanize_datetime.py
│   │   ├── __init__.py
│   │   ├── json.py
│   │   ├── mediatypes.py
│   │   ├── model_meta.py
│   │   ├── representation.py
│   │   ├── serializer_helpers.py
│   │   └── urls.py
│   ├── validators.py
│   ├── versioning.py
│   ├── viewsets.py
│   └── views.py
├── runtests.py
├── SECURITY.md
├── setup.cfg
├── setup.py
├── tests
│   ├── authentication
│   │   ├── __init__.py
│   │   ├── migrations
│   │   │   ├── 0001_initial.py
│   │   │   └── __init__.py
│   │   ├── models.py
│   │   └── test_authentication.py
│   ├── browsable_api
│   │   ├── auth_urls.py
│   │   ├── __init__.py
│   │   ├── no_auth_urls.py
│   │   ├── test_browsable_api.py
│   │   ├── test_browsable_nested_api.py
│   │   ├── test_form_rendering.py
│   │   └── views.py
│   ├── conftest.py
│   ├── generic_relations
│   │   ├── __init__.py
│   │   ├── migrations
│   │   │   ├── 0001_initial.py
│   │   │   └── __init__.py
│   │   ├── models.py
│   │   └── test_generic_relations.py
│   ├── importable
│   │   ├── __init__.py
│   │   └── test_installed.py
│   ├── __init__.py
│   ├── models.py
│   ├── schemas
│   │   ├── __init__.py
│   │   ├── test_coreapi.py
│   │   ├── test_get_schema_view.py
│   │   ├── test_managementcommand.py
│   │   ├── test_openapi.py
│   │   └── views.py
│   ├── test_api_client.py
│   ├── test_atomic_requests.py
│   ├── test_authtoken.py
│   ├── test_bound_fields.py
│   ├── test_decorators.py
│   ├── test_description.py
│   ├── test_encoders.py
│   ├── test_exceptions.py
│   ├── test_fields.py
│   ├── test_filters.py
│   ├── test_generics.py
│   ├── test_htmlrenderer.py
│   ├── test_lazy_hyperlinks.py
│   ├── test_metadata.py
│   ├── test_middleware.py
│   ├── test_model_serializer.py
│   ├── test_multitable_inheritance.py
│   ├── test_negotiation.py
│   ├── test_one_to_one_with_inheritance.py
│   ├── test_pagination.py
│   ├── test_parsers.py
│   ├── test_permissions.py
│   ├── test_prefetch_related.py
│   ├── test_relations_hyperlink.py
│   ├── test_relations_pk.py
│   ├── test_relations.py
│   ├── test_relations_slug.py
│   ├── test_renderers.py
│   ├── test_request.py
│   ├── test_requests_client.py
│   ├── test_response.py
│   ├── test_reverse.py
│   ├── test_routers.py
│   ├── test_serializer_bulk_update.py
│   ├── test_serializer_lists.py
│   ├── test_serializer_nested.py
│   ├── test_serializer.py
│   ├── test_settings.py
│   ├── test_status.py
│   ├── test_templates.py
│   ├── test_templatetags.py
│   ├── test_testing.py
│   ├── test_throttling.py
│   ├── test_urlpatterns.py
│   ├── test_utils.py
│   ├── test_validation_error.py
│   ├── test_validation.py
│   ├── test_validators.py
│   ├── test_versioning.py
│   ├── test_viewsets.py
│   ├── test_views.py
│   ├── test_write_only_fields.py
│   ├── urls.py
│   └── utils.py
└── tox.ini
