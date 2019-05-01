# Third Party Packages

> Software ecosystems […] establish a community that further accelerates the sharing of knowledge, content, issues, expertise and skills.
>
> &mdash; [Jan Bosch][cite].

## About Third Party Packages

Third Party Packages allow developers to share code that extends the functionality of Django REST framework, in order to support additional use-cases.

We **support**, **encourage** and **strongly favor** the creation of Third Party Packages to encapsulate new behavior rather than adding additional functionality directly to Django REST Framework.

We aim to make creating third party packages as easy as possible, whilst keeping a **simple** and **well maintained** core API. By promoting third party packages we ensure that the responsibility for a package remains with its author. If a package proves suitably popular it can always be considered for inclusion into the core REST framework.

If you have an idea for a new feature please consider how it may be packaged as a Third Party Package. We're always happy to discuss ideas on the [Mailing List][discussion-group].

## How to create a Third Party Package

### Creating your package

You can use [this cookiecutter template][cookiecutter] for creating reusable Django REST Framework packages quickly. Cookiecutter creates projects from project templates. While optional, this cookiecutter template includes best practices from Django REST framework and other packages, as well as a Travis CI configuration, Tox configuration, and a sane setup.py for easy PyPI registration/distribution.

Note: Let us know if you have an alternate cookiecuter package so we can also link to it.

#### Running the initial cookiecutter command

To run the initial cookiecutter command, you'll first need to install the Python `cookiecutter` package.

    $ pip install cookiecutter

Once `cookiecutter` is installed just run the following to create a new project.

    $ cookiecutter gh:jpadilla/cookiecutter-django-rest-framework

You'll be prompted for some questions, answer them, then it'll create your Python package in the current working directory based on those values.

    full_name (default is "Your full name here")? Johnny Appleseed
    email (default is "you@example.com")? jappleseed@example.com
    github_username (default is "yourname")? jappleseed
    pypi_project_name (default is "dj-package")? djangorestframework-custom-auth
    repo_name (default is "dj-package")? django-rest-framework-custom-auth
    app_name (default is "djpackage")? custom_auth
    project_short_description (default is "Your project description goes here")?
    year (default is "2014")?
    version (default is "0.1.0")?

#### Getting it onto GitHub

To put your project up on GitHub, you'll need a repository for it to live in. You can create a new repository [here][new-repo]. If you need help, check out the [Create A Repo][create-a-repo] article on GitHub.


#### Adding to Travis CI

We recommend using [Travis CI][travis-ci], a hosted continuous integration service which integrates well with GitHub and is free for public repositories.

To get started with Travis CI, [sign in][travis-ci] with your GitHub account. Once you're signed in, go to your [profile page][travis-profile] and enable the service hook for the repository you want.

If you use the cookiecutter template, your project will already contain a `.travis.yml` file which Travis CI will use to build your project and run tests.  By default, builds are triggered everytime you push to your repository or create Pull Request.

#### Uploading to PyPI

Once you've got at least a prototype working and tests running, you should publish it on PyPI to allow others to install it via `pip`.

You must [register][pypi-register] an account before publishing to PyPI.

To register your package on PyPI run the following command.

    $ python setup.py register

If this is the first time publishing to PyPI, you'll be prompted to login.

Note: Before publishing you'll need to make sure you have the latest pip that supports `wheel` as well as install the `wheel` package.

    $ pip install --upgrade pip
    $ pip install wheel

After this, every time you want to release a new version on PyPI just run the following command.

    $ python setup.py publish
    You probably want to also tag the version now:
        git tag -a {0} -m 'version 0.1.0'
        git push --tags

After releasing a new version to PyPI, it's always a good idea to tag the version and make available as a GitHub Release.

We recommend to follow [Semantic Versioning][semver] for your package's versions.

### Development

#### Version requirements

The cookiecutter template assumes a set of supported versions will be provided for Python and Django. Make sure you correctly update your requirements, docs, `tox.ini`, `.travis.yml`, and `setup.py` to match the set of versions you wish to support.

#### Tests

The cookiecutter template includes a `runtests.py` which uses the `pytest` package as a test runner.

Before running, you'll need to install a couple test requirements.

    $ pip install -r requirements.txt

Once requirements installed, you can run `runtests.py`.

    $ ./runtests.py

Run using a more concise output style.

    $ ./runtests.py -q

Run the tests using a more concise output style, no coverage, no flake8.

    $ ./runtests.py --fast

Don't run the flake8 code linting.

    $ ./runtests.py --nolint

Only run the flake8 code linting, don't run the tests.

    $ ./runtests.py --lintonly

Run the tests for a given test case.

    $ ./runtests.py MyTestCase

Run the tests for a given test method.

    $ ./runtests.py MyTestCase.test_this_method

Shorter form to run the tests for a given test method.

    $ ./runtests.py test_this_method

To run your tests against multiple versions of Python as different versions of requirements such as Django we recommend using `tox`. [Tox][tox-docs] is a generic virtualenv management and test command line tool.

First, install `tox` globally.

    $ pip install tox

To run `tox`, just simply run:

    $ tox

To run a particular `tox` environment:

    $ tox -e envlist

`envlist` is a comma-separated value to that specifies the environments to run tests against. To view a list of all possible test environments, run:

    $ tox -l

#### Version compatibility

Sometimes, in order to ensure your code works on various different versions of Django, Python or third party libraries, you'll need to run slightly different code depending on the environment. Any code that branches in this way should be isolated into a `compat.py` module, and should provide a single common interface that the rest of the codebase can use.

Check out Django REST framework's [compat.py][drf-compat] for an example.

### Once your package is available

Once your package is decently documented and available on PyPI, you might want share it with others that might find it useful.

#### Adding to the Django REST framework grid

We suggest adding your package to the [REST Framework][rest-framework-grid] grid on Django Packages.

#### Adding to the Django REST framework docs

Create a [Pull Request][drf-create-pr] or [Issue][drf-create-issue] on GitHub, and we'll add a link to it from the main REST framework documentation. You can add your package under **Third party packages** of the API Guide section that best applies, like [Authentication][authentication] or [Permissions][permissions]. You can also link your package under the [Third Party Packages][third-party-packages] section.

#### Announce on the discussion group.

You can also let others know about your package through the [discussion group][discussion-group].

## Existing Third Party Packages

Django REST Framework has a growing community of developers, packages, and resources.

Check out a grid detailing all the packages and ecosystem around Django REST Framework at [Django Packages][rest-framework-grid].

To submit new content, [open an issue][drf-create-issue] or [create a pull request][drf-create-pr].

### Authentication

* [djangorestframework-digestauth][djangorestframework-digestauth] - Provides Digest Access Authentication support.
* [django-oauth-toolkit][django-oauth-toolkit] - Provides OAuth 2.0 support.
* [djangorestframework-simplejwt][djangorestframework-simplejwt] - Provides JSON Web Token Authentication support.
* [hawkrest][hawkrest] - Provides Hawk HTTP Authorization.
* [djangorestframework-httpsignature][djangorestframework-httpsignature] - Provides an easy to use HTTP Signature Authentication mechanism.
* [djoser][djoser] - Provides a set of views to handle basic actions such as registration, login, logout, password reset and account activation.
* [django-rest-auth][django-rest-auth] - Provides a set of REST API endpoints for registration, authentication (including social media authentication), password reset, retrieve and update user details, etc.
* [drf-oidc-auth][drf-oidc-auth] - Implements OpenID Connect token authentication for DRF.
* [drfpasswordless][drfpasswordless] - Adds (Medium, Square Cash inspired) passwordless logins and signups via email and mobile numbers.

### Permissions

* [drf-any-permissions][drf-any-permissions] - Provides alternative permission handling.
* [djangorestframework-composed-permissions][djangorestframework-composed-permissions] - Provides a simple way to define complex permissions.
* [rest_condition][rest-condition] - Another extension for building complex permissions in a simple and convenient way.
* [dry-rest-permissions][dry-rest-permissions] - Provides a simple way to define permissions for individual api actions.

### Serializers

* [django-rest-framework-mongoengine][django-rest-framework-mongoengine] - Serializer class that supports using MongoDB as the storage layer for Django REST framework.
* [djangorestframework-gis][djangorestframework-gis] - Geographic add-ons
* [djangorestframework-hstore][djangorestframework-hstore] - Serializer class to support django-hstore DictionaryField model field and its schema-mode feature.
* [djangorestframework-jsonapi][djangorestframework-jsonapi] - Provides a parser, renderer, serializers, and other tools to help build an API that is compliant with the jsonapi.org spec.
* [html-json-forms][html-json-forms] - Provides an algorithm and serializer to process HTML JSON Form submissions per the (inactive) spec.
* [django-rest-framework-serializer-extensions][drf-serializer-extensions] -
  Enables black/whitelisting fields, and conditionally expanding child serializers on a per-view/request basis.
* [djangorestframework-queryfields][djangorestframework-queryfields] - Serializer mixin allowing clients to control which fields will be sent in the API response.

### Serializer fields

* [drf-compound-fields][drf-compound-fields] - Provides "compound" serializer fields, such as lists of simple values.
* [django-extra-fields][django-extra-fields] - Provides extra serializer fields.
* [django-versatileimagefield][django-versatileimagefield] - Provides a drop-in replacement for Django's stock `ImageField` that makes it easy to serve images in multiple sizes/renditions from a single field. For DRF-specific implementation docs, [click here][django-versatileimagefield-drf-docs].

### Views

* [djangorestframework-bulk][djangorestframework-bulk] - Implements generic view mixins as well as some common concrete generic views to allow to apply bulk operations via API requests.
* [django-rest-multiple-models][django-rest-multiple-models] - Provides a generic view (and mixin) for sending multiple serialized models and/or querysets via a single API request.

### Routers

* [drf-nested-routers][drf-nested-routers] - Provides routers and relationship fields for working with nested resources.
* [wq.db.rest][wq.db.rest] - Provides an admin-style model registration API with reasonable default URLs and viewsets.

### Parsers

* [djangorestframework-msgpack][djangorestframework-msgpack] - Provides MessagePack renderer and parser support.
* [djangorestframework-jsonapi][djangorestframework-jsonapi] - Provides a parser, renderer, serializers, and other tools to help build an API that is compliant with the jsonapi.org spec.
* [djangorestframework-camel-case][djangorestframework-camel-case] - Provides camel case JSON renderers and parsers.

### Renderers

* [djangorestframework-csv][djangorestframework-csv] - Provides CSV renderer support.
* [djangorestframework-jsonapi][djangorestframework-jsonapi] - Provides a parser, renderer, serializers, and other tools to help build an API that is compliant with the jsonapi.org spec.
* [drf_ujson][drf_ujson] - Implements JSON rendering using the UJSON package.
* [rest-pandas][rest-pandas] - Pandas DataFrame-powered renderers including Excel, CSV, and SVG formats.
* [djangorestframework-rapidjson][djangorestframework-rapidjson] - Provides rapidjson support with parser and renderer.

### Filtering

* [djangorestframework-chain][djangorestframework-chain] - Allows arbitrary chaining of both relations and lookup filters.
* [django-url-filter][django-url-filter] - Allows a safe way to filter data via human-friendly URLs. It is a generic library which is not tied to DRF but it provides easy integration with DRF.
* [drf-url-filter][drf-url-filter] is a simple Django app to apply filters on drf `ModelViewSet`'s `Queryset` in a clean, simple and configurable way. It also supports validations on incoming query params and their values.

### Misc

* [cookiecutter-django-rest][cookiecutter-django-rest] - A cookiecutter template that takes care of the setup and configuration so you can focus on making your REST apis awesome.
* [djangorestrelationalhyperlink][djangorestrelationalhyperlink] - A hyperlinked serialiser that can can be used to alter relationships via hyperlinks, but otherwise like a hyperlink model serializer.
* [django-rest-swagger][django-rest-swagger] - An API documentation generator for Swagger UI.
* [django-rest-framework-proxy][django-rest-framework-proxy] - Proxy to redirect incoming request to another API server.
* [gaiarestframework][gaiarestframework] - Utils for django-rest-framework
* [drf-extensions][drf-extensions] - A collection of custom extensions
* [ember-django-adapter][ember-django-adapter] - An adapter for working with Ember.js
* [django-versatileimagefield][django-versatileimagefield] - Provides a drop-in replacement for Django's stock `ImageField` that makes it easy to serve images in multiple sizes/renditions from a single field. For DRF-specific implementation docs, [click here][django-versatileimagefield-drf-docs].
* [drf-tracking][drf-tracking] - Utilities to track requests to DRF API views.
* [drf_tweaks][drf_tweaks] - Serializers with one-step validation (and more), pagination without counts and other tweaks.
* [django-rest-framework-braces][django-rest-framework-braces] - Collection of utilities for working with Django Rest Framework. The most notable ones are [FormSerializer](https://django-rest-framework-braces.readthedocs.io/en/latest/overview.html#formserializer) and [SerializerForm](https://django-rest-framework-braces.readthedocs.io/en/latest/overview.html#serializerform), which are adapters between DRF serializers and Django forms.
* [drf-haystack][drf-haystack] - Haystack search for Django Rest Framework
* [django-rest-framework-version-transforms][django-rest-framework-version-transforms] - Enables the use of delta transformations for versioning of DRF resource representations.
* [django-rest-messaging][django-rest-messaging], [django-rest-messaging-centrifugo][django-rest-messaging-centrifugo] and [django-rest-messaging-js][django-rest-messaging-js] - A real-time pluggable messaging service using DRM.
* [djangorest-alchemy][djangorest-alchemy] - SQLAlchemy support for REST framework.
* [djangorestframework-datatables][djangorestframework-datatables] - Seamless integration between Django REST framework and [Datatables](https://datatables.net).
* [django-rest-framework-condition][django-rest-framework-condition] - Decorators for managing HTTP cache headers for Django REST framework (ETag and Last-modified).

[cite]: http://www.software-ecosystems.com/Software_Ecosystems/Ecosystems.html
[cookiecutter]: https://github.com/jpadilla/cookiecutter-django-rest-framework
[new-repo]: https://github.com/new
[create-a-repo]: https://help.github.com/articles/create-a-repo/
[travis-ci]: https://travis-ci.org
[travis-profile]: https://travis-ci.org/profile
[pypi-register]: https://pypi.org/account/register/
[semver]: https://semver.org/
[tox-docs]: https://tox.readthedocs.io/en/latest/
[drf-compat]: https://github.com/encode/django-rest-framework/blob/master/rest_framework/compat.py
[rest-framework-grid]: https://www.djangopackages.com/grids/g/django-rest-framework/
[drf-create-pr]: https://github.com/encode/django-rest-framework/compare
[drf-create-issue]: https://github.com/encode/django-rest-framework/issues/new
[authentication]: ../api-guide/authentication.md
[permissions]: ../api-guide/permissions.md
[third-party-packages]: ../topics/third-party-packages/#existing-third-party-packages
[discussion-group]: https://groups.google.com/forum/#!forum/django-rest-framework
[djangorestframework-digestauth]: https://github.com/juanriaza/django-rest-framework-digestauth
[django-oauth-toolkit]: https://github.com/evonove/django-oauth-toolkit
[djangorestframework-jwt]: https://github.com/GetBlimp/django-rest-framework-jwt
[djangorestframework-simplejwt]: https://github.com/davesque/django-rest-framework-simplejwt
[hawkrest]: https://github.com/kumar303/hawkrest
[djangorestframework-httpsignature]: https://github.com/etoccalino/django-rest-framework-httpsignature
[djoser]: https://github.com/sunscrapers/djoser
[drf-any-permissions]: https://github.com/kevin-brown/drf-any-permissions
[djangorestframework-composed-permissions]: https://github.com/niwibe/djangorestframework-composed-permissions
[rest-condition]: https://github.com/caxap/rest_condition
[django-rest-framework-mongoengine]: https://github.com/umutbozkurt/django-rest-framework-mongoengine
[djangorestframework-gis]: https://github.com/djangonauts/django-rest-framework-gis
[djangorestframework-hstore]: https://github.com/djangonauts/django-rest-framework-hstore
[drf-compound-fields]: https://github.com/estebistec/drf-compound-fields
[django-extra-fields]: https://github.com/Hipo/drf-extra-fields
[djangorestframework-bulk]: https://github.com/miki725/django-rest-framework-bulk
[django-rest-multiple-models]: https://github.com/MattBroach/DjangoRestMultipleModels
[drf-nested-routers]: https://github.com/alanjds/drf-nested-routers
[wq.db.rest]: https://wq.io/docs/about-rest
[djangorestframework-msgpack]: https://github.com/juanriaza/django-rest-framework-msgpack
[djangorestframework-camel-case]: https://github.com/vbabiy/djangorestframework-camel-case
[djangorestframework-csv]: https://github.com/mjumbewu/django-rest-framework-csv
[drf_ujson]: https://github.com/gizmag/drf-ujson-renderer
[rest-pandas]: https://github.com/wq/django-rest-pandas
[djangorestframework-rapidjson]: https://github.com/allisson/django-rest-framework-rapidjson
[djangorestframework-chain]: https://github.com/philipn/django-rest-framework-chain
[djangorestrelationalhyperlink]: https://github.com/fredkingham/django_rest_model_hyperlink_serializers_project
[django-rest-swagger]: https://github.com/marcgibbons/django-rest-swagger
[django-rest-framework-proxy]: https://github.com/eofs/django-rest-framework-proxy
[gaiarestframework]: https://github.com/AppsFuel/gaiarestframework
[drf-extensions]: https://github.com/chibisov/drf-extensions
[ember-django-adapter]: https://github.com/dustinfarris/ember-django-adapter
[django-rest-auth]: https://github.com/Tivix/django-rest-auth/
[django-versatileimagefield]: https://github.com/WGBH/django-versatileimagefield
[django-versatileimagefield-drf-docs]:https://django-versatileimagefield.readthedocs.io/en/latest/drf_integration.html
[drf-tracking]: https://github.com/aschn/drf-tracking
[django-rest-framework-braces]: https://github.com/dealertrack/django-rest-framework-braces
[dry-rest-permissions]: https://github.com/Helioscene/dry-rest-permissions
[django-url-filter]: https://github.com/miki725/django-url-filter
[drf-url-filter]: https://github.com/manjitkumar/drf-url-filters
[cookiecutter-django-rest]:  https://github.com/agconti/cookiecutter-django-rest
[drf-haystack]: https://drf-haystack.readthedocs.io/en/latest/
[django-rest-framework-version-transforms]: https://github.com/mrhwick/django-rest-framework-version-transforms
[djangorestframework-jsonapi]: https://github.com/django-json-api/django-rest-framework-json-api
[html-json-forms]: https://github.com/wq/html-json-forms
[django-rest-messaging]: https://github.com/raphaelgyory/django-rest-messaging
[django-rest-messaging-centrifugo]: https://github.com/raphaelgyory/django-rest-messaging-centrifugo
[django-rest-messaging-js]: https://github.com/raphaelgyory/django-rest-messaging-js
[drf_tweaks]: https://github.com/ArabellaTech/drf_tweaks
[drf-oidc-auth]: https://github.com/ByteInternet/drf-oidc-auth
[drf-serializer-extensions]: https://github.com/evenicoulddoit/django-rest-framework-serializer-extensions
[djangorestframework-queryfields]: https://github.com/wimglenn/djangorestframework-queryfields
[drfpasswordless]: https://github.com/aaronn/django-rest-framework-passwordless
[djangorest-alchemy]: https://github.com/dealertrack/djangorest-alchemy
[djangorestframework-datatables]: https://github.com/izimobil/django-rest-framework-datatables
[django-rest-framework-condition]: https://github.com/jozo/django-rest-framework-condition
