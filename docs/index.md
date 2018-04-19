<style>
.promo li a {
    float: left;
    width: 130px;
    height: 20px;
    text-align: center;
    margin: 10px 30px;
    padding: 150px 0 0 0;
    background-position: 0 50%;
    background-size: 130px auto;
    background-repeat: no-repeat;
    font-size: 120%;
    color: black;
}
.promo li {
    list-style: none;
}
</style>

<p class="badges" height=20px>
    <iframe src="https://ghbtns.com/github-btn.html?user=encode&amp;repo=django-rest-framework&amp;type=watch&amp;count=true" class="github-star-button" allowtransparency="true" frameborder="0" scrolling="0" width="110px" height="20px"></iframe>

    <a href="https://travis-ci.org/encode/django-rest-framework?branch=master">
        <img src="https://secure.travis-ci.org/encode/django-rest-framework.svg?branch=master" class="status-badge">
    </a>

    <a href="https://pypi.org/project/djangorestframework/">
        <img src="https://img.shields.io/pypi/v/djangorestframework.svg" class="status-badge">
    </a>
</p>

---

**Note**: This is the documentation for the **version 3** of REST framework. Documentation for [version 2](https://tomchristie.github.io/rest-framework-2-docs/) is also available.

---

<p>
<h1 style="position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0,0,0,0);
    border: 0;">Django REST Framework</h1>

<img alt="Django REST Framework" title="Logo by Jake 'Sid' Smith" src="img/logo.png" width="600px" style="display: block; margin: 0 auto 0 auto">
</p>

Django REST framework is a powerful and flexible toolkit for building Web APIs.

Some reasons you might want to use REST framework:

* The [Web browsable API][sandbox] is a huge usability win for your developers.
* [Authentication policies][authentication] including packages for [OAuth1a][oauth1-section] and [OAuth2][oauth2-section].
* [Serialization][serializers] that supports both [ORM][modelserializer-section] and [non-ORM][serializer-section] data sources.
* Customizable all the way down - just use [regular function-based views][functionview-section] if you don't need the [more][generic-views] [powerful][viewsets] [features][routers].
* [Extensive documentation][index], and [great community support][group].
* Used and trusted by internationally recognised companies including [Mozilla][mozilla], [Red Hat][redhat], [Heroku][heroku], and [Eventbrite][eventbrite].

---

## Funding

REST framework is a *collaboratively funded project*. If you use
REST framework commercially we strongly encourage you to invest in its
continued development by **[signing up for a paid plan][funding]**.

*Every single sign-up helps us make REST framework long-term financially sustainable.*

<ul class="premium-promo promo">
    <li><a href="http://jobs.rover.com/" style="background-image: url(https://fund-rest-framework.s3.amazonaws.com/rover_130x130.png)">Rover.com</a></li>
    <li><a href="https://getsentry.com/welcome/" style="background-image: url(https://fund-rest-framework.s3.amazonaws.com/sentry130.png)">Sentry</a></li>
    <li><a href="https://getstream.io/try-the-api/?utm_source=drf&utm_medium=banner&utm_campaign=drf" style="background-image: url(https://fund-rest-framework.s3.amazonaws.com/stream-130.png)">Stream</a></li>
    <li><a href="https://hello.machinalis.co.uk/" style="background-image: url(https://fund-rest-framework.s3.amazonaws.com/Machinalis130.png)">Machinalis</a></li>
    <li><a href="https://rollbar.com" style="background-image: url(https://fund-rest-framework.s3.amazonaws.com/rollbar2.png)">Rollbar</a></li>
    <li><a href="https://cadre.com" style="background-image: url(https://fund-rest-framework.s3.amazonaws.com/cadre.png)">Cadre</a></li>
</ul>
<div style="clear: both; padding-bottom: 20px;"></div>

*Many thanks to all our [wonderful sponsors][sponsors], and in particular to our premium backers, [Rover](http://jobs.rover.com/), [Sentry](https://getsentry.com/welcome/), [Stream](https://getstream.io/?utm_source=drf&utm_medium=banner&utm_campaign=drf), [Machinalis](https://hello.machinalis.co.uk/), [Rollbar](https://rollbar.com), and [Cadre](https://cadre.com).*

---

## Requirements

REST framework requires the following:

* Python (2.7, 3.2, 3.3, 3.4, 3.5, 3.6)
* Django (1.10, 1.11, 2.0)

The following packages are optional:

* [coreapi][coreapi] (1.32.0+) - Schema generation support.
* [Markdown][markdown] (2.1.0+) - Markdown support for the browsable API.
* [django-filter][django-filter] (1.0.1+) - Filtering support.
* [django-crispy-forms][django-crispy-forms] - Improved HTML display for filtering.
* [django-guardian][django-guardian] (1.1.1+) - Object level permissions support.

## Installation

Install using `pip`, including any optional packages you want...

    pip install djangorestframework
    pip install markdown       # Markdown support for the browsable API.
    pip install django-filter  # Filtering support

...or clone the project from github.

    git clone git@github.com:encode/django-rest-framework.git

Add `'rest_framework'` to your `INSTALLED_APPS` setting.

    INSTALLED_APPS = (
        ...
        'rest_framework',
    )

If you're intending to use the browsable API you'll probably also want to add REST framework's login and logout views.  Add the following to your root `urls.py` file.

    urlpatterns = [
        ...
        url(r'^api-auth/', include('rest_framework.urls'))
    ]

Note that the URL path can be whatever you want.

## Example

Let's take a look at a quick example of using REST framework to build a simple model-backed API.

We'll create a read-write API for accessing information on the users of our project.

Any global settings for a REST framework API are kept in a single configuration dictionary named `REST_FRAMEWORK`.  Start off by adding the following to your `settings.py` module:

    REST_FRAMEWORK = {
        # Use Django's standard `django.contrib.auth` permissions,
        # or allow read-only access for unauthenticated users.
        'DEFAULT_PERMISSION_CLASSES': [
            'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
        ]
    }

Don't forget to make sure you've also added `rest_framework` to your `INSTALLED_APPS`.

We're ready to create our API now.
Here's our project's root `urls.py` module:

    from django.conf.urls import url, include
    from django.contrib.auth.models import User
    from rest_framework import routers, serializers, viewsets

	# Serializers define the API representation.
	class UserSerializer(serializers.HyperlinkedModelSerializer):
	    class Meta:
	        model = User
	        fields = ('url', 'username', 'email', 'is_staff')

    # ViewSets define the view behavior.
    class UserViewSet(viewsets.ModelViewSet):
        queryset = User.objects.all()
        serializer_class = UserSerializer

    # Routers provide an easy way of automatically determining the URL conf.
    router = routers.DefaultRouter()
    router.register(r'users', UserViewSet)

    # Wire up our API using automatic URL routing.
    # Additionally, we include login URLs for the browsable API.
    urlpatterns = [
        url(r'^', include(router.urls)),
        url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
    ]

You can now open the API in your browser at [http://127.0.0.1:8000/](http://127.0.0.1:8000/), and view your new 'users' API. If you use the login control in the top right corner you'll also be able to add, create and delete users from the system.

## Quickstart

Can't wait to get started? The [quickstart guide][quickstart] is the fastest way to get up and running, and building APIs with REST framework.

## Tutorial

The tutorial will walk you through the building blocks that make up REST framework.   It'll take a little while to get through, but it'll give you a comprehensive understanding of how everything fits together, and is highly recommended reading.

* [1 - Serialization][tut-1]
* [2 - Requests & Responses][tut-2]
* [3 - Class-based views][tut-3]
* [4 - Authentication & permissions][tut-4]
* [5 - Relationships & hyperlinked APIs][tut-5]
* [6 - Viewsets & routers][tut-6]
* [7 - Schemas & client libraries][tut-7]

There is a live example API of the finished tutorial API for testing purposes, [available here][sandbox].

## API Guide

The API guide is your complete reference manual to all the functionality provided by REST framework.

* [Requests][request]
* [Responses][response]
* [Views][views]
* [Generic views][generic-views]
* [Viewsets][viewsets]
* [Routers][routers]
* [Parsers][parsers]
* [Renderers][renderers]
* [Serializers][serializers]
* [Serializer fields][fields]
* [Serializer relations][relations]
* [Validators][validators]
* [Authentication][authentication]
* [Permissions][permissions]
* [Throttling][throttling]
* [Filtering][filtering]
* [Pagination][pagination]
* [Versioning][versioning]
* [Content negotiation][contentnegotiation]
* [Metadata][metadata]
* [Schemas][schemas]
* [Format suffixes][formatsuffixes]
* [Returning URLs][reverse]
* [Exceptions][exceptions]
* [Status codes][status]
* [Testing][testing]
* [Settings][settings]

## Topics

General guides to using REST framework.

* [Documenting your API][documenting-your-api]
* [API Clients][api-clients]
* [Internationalization][internationalization]
* [AJAX, CSRF & CORS][ajax-csrf-cors]
* [HTML & Forms][html-and-forms]
* [Browser enhancements][browser-enhancements]
* [The Browsable API][browsableapi]
* [REST, Hypermedia & HATEOAS][rest-hypermedia-hateoas]
* [Third Party Packages][third-party-packages]
* [Tutorials and Resources][tutorials-and-resources]
* [Contributing to REST framework][contributing]
* [Project management][project-management]
* [3.0 Announcement][3.0-announcement]
* [3.1 Announcement][3.1-announcement]
* [3.2 Announcement][3.2-announcement]
* [3.3 Announcement][3.3-announcement]
* [3.4 Announcement][3.4-announcement]
* [3.5 Announcement][3.5-announcement]
* [3.6 Announcement][3.6-announcement]
* [3.7 Announcement][3.7-announcement]
* [3.8 Announcement][3.8-announcement]
* [Kickstarter Announcement][kickstarter-announcement]
* [Mozilla Grant][mozilla-grant]
* [Funding][funding]
* [Release Notes][release-notes]
* [Jobs][jobs]

## Development

See the [Contribution guidelines][contributing] for information on how to clone
the repository, run the test suite and contribute changes back to REST
Framework.

## Support

For support please see the [REST framework discussion group][group], try the  `#restframework` channel on `irc.freenode.net`, search [the IRC archives][botbot], or raise a  question on [Stack Overflow][stack-overflow], making sure to include the ['django-rest-framework'][django-rest-framework-tag] tag.

For priority support please sign up for a [professional or premium sponsorship plan](https://fund.django-rest-framework.org/topics/funding/).

For updates on REST framework development, you may also want to follow [the author][twitter] on Twitter.

<a style="padding-top: 10px" href="https://twitter.com/_tomchristie" class="twitter-follow-button" data-show-count="false">Follow @_tomchristie</a>
<script>!function(d,s,id){var js,fjs=d.getElementsByTagName(s)[0];if(!d.getElementById(id)){js=d.createElement(s);js.id=id;js.src="//platform.twitter.com/widgets.js";fjs.parentNode.insertBefore(js,fjs);}}(document,"script","twitter-wjs");</script>

## Security

If you believe you’ve found something in Django REST framework which has security implications, please **do not raise the issue in a public forum**.

Send a description of the issue via email to [rest-framework-security@googlegroups.com][security-mail].  The project maintainers will then work with you to resolve any issues where required, prior to any public disclosure.

## License

Copyright (c) 2011-2017, Tom Christie
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

[mozilla]: https://www.mozilla.org/en-US/about/
[redhat]: https://www.redhat.com/
[heroku]: https://www.heroku.com/
[eventbrite]: https://www.eventbrite.co.uk/about/
[coreapi]: https://pypi.org/project/coreapi/
[markdown]: https://pypi.org/project/Markdown/
[django-filter]: https://pypi.org/project/django-filter/
[django-crispy-forms]: https://github.com/maraujop/django-crispy-forms
[django-guardian]: https://github.com/django-guardian/django-guardian
[index]: .
[oauth1-section]: api-guide/authentication/#django-rest-framework-oauth
[oauth2-section]: api-guide/authentication/#django-oauth-toolkit
[serializer-section]: api-guide/serializers#serializers
[modelserializer-section]: api-guide/serializers#modelserializer
[functionview-section]: api-guide/views#function-based-views
[sandbox]: https://restframework.herokuapp.com/
[sponsors]: https://fund.django-rest-framework.org/topics/funding/#our-sponsors

[quickstart]: tutorial/quickstart.md
[tut-1]: tutorial/1-serialization.md
[tut-2]: tutorial/2-requests-and-responses.md
[tut-3]: tutorial/3-class-based-views.md
[tut-4]: tutorial/4-authentication-and-permissions.md
[tut-5]: tutorial/5-relationships-and-hyperlinked-apis.md
[tut-6]: tutorial/6-viewsets-and-routers.md
[tut-7]: tutorial/7-schemas-and-client-libraries.md

[request]: api-guide/requests.md
[response]: api-guide/responses.md
[views]: api-guide/views.md
[generic-views]: api-guide/generic-views.md
[viewsets]: api-guide/viewsets.md
[routers]: api-guide/routers.md
[parsers]: api-guide/parsers.md
[renderers]: api-guide/renderers.md
[serializers]: api-guide/serializers.md
[fields]: api-guide/fields.md
[relations]: api-guide/relations.md
[validators]: api-guide/validators.md
[authentication]: api-guide/authentication.md
[permissions]: api-guide/permissions.md
[throttling]: api-guide/throttling.md
[filtering]: api-guide/filtering.md
[pagination]: api-guide/pagination.md
[versioning]: api-guide/versioning.md
[contentnegotiation]: api-guide/content-negotiation.md
[metadata]: api-guide/metadata.md
[schemas]: api-guide/schemas.md
[formatsuffixes]: api-guide/format-suffixes.md
[reverse]: api-guide/reverse.md
[exceptions]: api-guide/exceptions.md
[status]: api-guide/status-codes.md
[testing]: api-guide/testing.md
[settings]: api-guide/settings.md

[documenting-your-api]: topics/documenting-your-api.md
[api-clients]: topics/api-clients.md
[internationalization]: topics/internationalization.md
[ajax-csrf-cors]: topics/ajax-csrf-cors.md
[html-and-forms]: topics/html-and-forms.md
[browser-enhancements]: topics/browser-enhancements.md
[browsableapi]: topics/browsable-api.md
[rest-hypermedia-hateoas]: topics/rest-hypermedia-hateoas.md
[contributing]: topics/contributing.md
[project-management]: topics/project-management.md
[third-party-packages]: topics/third-party-packages.md
[tutorials-and-resources]: topics/tutorials-and-resources.md
[3.0-announcement]: topics/3.0-announcement.md
[3.1-announcement]: topics/3.1-announcement.md
[3.2-announcement]: topics/3.2-announcement.md
[3.3-announcement]: topics/3.3-announcement.md
[3.4-announcement]: topics/3.4-announcement.md
[3.5-announcement]: topics/3.5-announcement.md
[3.6-announcement]: topics/3.6-announcement.md
[3.7-announcement]: topics/3.7-announcement.md
[3.8-announcement]: topics/3.8-announcement.md
[kickstarter-announcement]: topics/kickstarter-announcement.md
[mozilla-grant]: topics/mozilla-grant.md
[funding]: topics/funding.md
[release-notes]: topics/release-notes.md
[jobs]: topics/jobs.md

[group]: https://groups.google.com/forum/?fromgroups#!forum/django-rest-framework
[botbot]: https://botbot.me/freenode/restframework/
[stack-overflow]: https://stackoverflow.com/
[django-rest-framework-tag]: https://stackoverflow.com/questions/tagged/django-rest-framework
[security-mail]: mailto:rest-framework-security@googlegroups.com
[twitter]: https://twitter.com/_tomchristie
