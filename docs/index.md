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

    <a href="https://github.com/encode/django-rest-framework/actions/workflows/main.yml">
        <img src="https://github.com/encode/django-rest-framework/actions/workflows/main.yml/badge.svg" class="status-badge">
    </a>

    <a href="https://pypi.org/project/djangorestframework/">
        <img src="https://img.shields.io/pypi/v/djangorestframework.svg" class="status-badge">
    </a>
</p>

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

* The Web browsable API is a huge usability win for your developers.
* [Authentication policies][authentication] including packages for [OAuth1a][oauth1-section] and [OAuth2][oauth2-section].
* [Serialization][serializers] that supports both [ORM][modelserializer-section] and [non-ORM][serializer-section] data sources.
* Customizable all the way down - just use [regular function-based views][functionview-section] if you don't need the [more][generic-views] [powerful][viewsets] [features][routers].
* Extensive documentation, and [great community support][group].
* Used and trusted by internationally recognised companies including [Mozilla][mozilla], [Red Hat][redhat], [Heroku][heroku], and [Eventbrite][eventbrite].

---

## Funding

REST framework is a *collaboratively funded project*. If you use
REST framework commercially we strongly encourage you to invest in its
continued development by **[signing up for a paid plan][funding]**.

*Every single sign-up helps us make REST framework long-term financially sustainable.*

<ul class="premium-promo promo">
    <li><a href="https://getsentry.com/welcome/" style="background-image: url(https://fund-rest-framework.s3.amazonaws.com/sentry130.png)">Sentry</a></li>
    <li><a href="https://getstream.io/?utm_source=DjangoRESTFramework&utm_medium=Webpage_Logo_Ad&utm_content=Developer&utm_campaign=DjangoRESTFramework_Jan2022_HomePage" style="background-image: url(https://fund-rest-framework.s3.amazonaws.com/stream-130.png)">Stream</a></li>
    <li><a href="https://www.spacinov.com/" style="background-image: url(https://fund-rest-framework.s3.amazonaws.com/spacinov.png)">Spacinov</a></li>
    <li><a href="https://retool.com/?utm_source=djangorest&utm_medium=sponsorship" style="background-image: url(https://fund-rest-framework.s3.amazonaws.com/retool-sidebar.png)">Retool</a></li>
    <li><a href="https://bit.io/jobs?utm_source=DRF&utm_medium=sponsor&utm_campaign=DRF_sponsorship" style="background-image: url(https://fund-rest-framework.s3.amazonaws.com/bitio_logo_gold_background.png)">bit.io</a></li>
    <li><a href="https://posthog.com?utm_source=DRF&utm_medium=sponsor&utm_campaign=DRF_sponsorship" style="background-image: url(https://fund-rest-framework.s3.amazonaws.com/135996800-d49fe024-32d9-441a-98d9-4c7596287a67.png)">PostHog</a></li>
    <li><a href="https://cryptapi.io" style="background-image: url(https://fund-rest-framework.s3.amazonaws.com/cryptapi.png)">CryptAPI</a></li>
    <li><a href="https://www.fezto.xyz/?utm_source=DjangoRESTFramework" style="background-image: url(https://fund-rest-framework.s3.amazonaws.com/fezto.png)">FEZTO</a></li>
    <li><a href="https://www.svix.com/?utm_source=django-REST&utm_medium=sponsorship" style="background-image: url(https://fund-rest-framework.s3.amazonaws.com/svix.png)">Svix</a></li>
    <li><a href="https://zuplo.link/django-web" style="background-image: url(https://fund-rest-framework.s3.amazonaws.com/zuplo.png)">Zuplo</a></li>
</ul>
<div style="clear: both; padding-bottom: 20px;"></div>

*Many thanks to all our [wonderful sponsors][sponsors], and in particular to our premium backers, [Sentry](https://getsentry.com/welcome/), [Stream](https://getstream.io/?utm_source=DjangoRESTFramework&utm_medium=Webpage_Logo_Ad&utm_content=Developer&utm_campaign=DjangoRESTFramework_Jan2022_HomePage), [Spacinov](https://www.spacinov.com/), [Retool](https://retool.com/?utm_source=djangorest&utm_medium=sponsorship), [bit.io](https://bit.io/jobs?utm_source=DRF&utm_medium=sponsor&utm_campaign=DRF_sponsorship), [PostHog](https://posthog.com?utm_source=DRF&utm_medium=sponsor&utm_campaign=DRF_sponsorship), [CryptAPI](https://cryptapi.io), [FEZTO](https://www.fezto.xyz/?utm_source=DjangoRESTFramework), [Svix](https://www.svix.com/?utm_source=django-REST&utm_medium=sponsorship), , and [Zuplo](https://zuplo.link/django-web).*

---

## Requirements

REST framework requires the following:

* Django (4.2, 5.0, 5.1)
* Python (3.8, 3.9, 3.10, 3.11, 3.12, 3.13)

We **highly recommend** and only officially support the latest patch release of
each Python and Django series.

The following packages are optional:

* [PyYAML][pyyaml], [uritemplate][uriteemplate] (5.1+, 3.0.0+) - Schema generation support.
* [Markdown][markdown] (3.3.0+) - Markdown support for the browsable API.
* [Pygments][pygments] (2.7.0+) - Add syntax highlighting to Markdown processing.
* [django-filter][django-filter] (1.0.1+) - Filtering support.
* [django-guardian][django-guardian] (1.1.1+) - Object level permissions support.

## Installation

Install using `pip`, including any optional packages you want...

    pip install djangorestframework
    pip install markdown       # Markdown support for the browsable API.
    pip install django-filter  # Filtering support

...or clone the project from github.

    git clone https://github.com/encode/django-rest-framework

Add `'rest_framework'` to your `INSTALLED_APPS` setting.

    INSTALLED_APPS = [
        ...
        'rest_framework',
    ]

If you're intending to use the browsable API you'll probably also want to add REST framework's login and logout views.  Add the following to your root `urls.py` file.

    urlpatterns = [
        ...
        path('api-auth/', include('rest_framework.urls'))
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

    from django.urls import path, include
    from django.contrib.auth.models import User
    from rest_framework import routers, serializers, viewsets

    # Serializers define the API representation.
    class UserSerializer(serializers.HyperlinkedModelSerializer):
        class Meta:
            model = User
            fields = ['url', 'username', 'email', 'is_staff']

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
        path('', include(router.urls)),
        path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
    ]

You can now open the API in your browser at [http://127.0.0.1:8000/](http://127.0.0.1:8000/), and view your new 'users' API. If you use the login control in the top right corner you'll also be able to add, create and delete users from the system.

## Quickstart

Can't wait to get started? The [quickstart guide][quickstart] is the fastest way to get up and running, and building APIs with REST framework.

## Development

See the [Contribution guidelines][contributing] for information on how to clone
the repository, run the test suite and help maintain the code base of REST
Framework.

## Support

For support please see the [REST framework discussion group][group], try the `#restframework` channel on `irc.libera.chat`, or raise a question on [Stack Overflow][stack-overflow], making sure to include the ['django-rest-framework'][django-rest-framework-tag] tag.

For priority support please sign up for a [professional or premium sponsorship plan](https://fund.django-rest-framework.org/topics/funding/).

## Security

**Please report security issues by emailing security@encode.io**.

The project maintainers will then work with you to resolve any issues where required, prior to any public disclosure.

## License

Copyright © 2011-present, [Encode OSS Ltd](https://www.encode.io/).
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

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
[pyyaml]: https://pypi.org/project/PyYAML/
[uriteemplate]: https://pypi.org/project/uritemplate/
[markdown]: https://pypi.org/project/Markdown/
[pygments]: https://pypi.org/project/Pygments/
[django-filter]: https://pypi.org/project/django-filter/
[django-guardian]: https://github.com/django-guardian/django-guardian
[index]: .
[oauth1-section]: api-guide/authentication/#django-rest-framework-oauth
[oauth2-section]: api-guide/authentication/#django-oauth-toolkit
[serializer-section]: api-guide/serializers#serializers
[modelserializer-section]: api-guide/serializers#modelserializer
[functionview-section]: api-guide/views#function-based-views
[sponsors]: https://fund.django-rest-framework.org/topics/funding/#our-sponsors

[quickstart]: tutorial/quickstart.md

[generic-views]: api-guide/generic-views.md
[viewsets]: api-guide/viewsets.md
[routers]: api-guide/routers.md
[serializers]: api-guide/serializers.md
[authentication]: api-guide/authentication.md

[contributing]: community/contributing.md
[funding]: community/funding.md

[group]: https://groups.google.com/forum/?fromgroups#!forum/django-rest-framework
[stack-overflow]: https://stackoverflow.com/
[django-rest-framework-tag]: https://stackoverflow.com/questions/tagged/django-rest-framework
[security-mail]: mailto:rest-framework-security@googlegroups.com
[twitter]: https://twitter.com/_tomchristie
