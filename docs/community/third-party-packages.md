# Third Party Packages

> Software ecosystems […] establish a community that further accelerates the sharing of knowledge, content, issues, expertise and skills.
>
> &mdash; [Jan Bosch][cite].

## About Third Party Packages

Third Party Packages allow developers to share code that extends the functionality of Django REST framework, in order to support additional use-cases.

We **support**, **encourage** and **strongly favor** the creation of Third Party Packages to encapsulate new behavior rather than adding additional functionality directly to Django REST Framework.

We aim to make creating third party packages as easy as possible, whilst keeping a **simple** and **well maintained** core API. By promoting third party packages we ensure that the responsibility for a package remains with its author. If a package proves suitably popular it can always be considered for inclusion into the core REST framework.

If you have an idea for a new feature please consider how it may be packaged as a Third Party Package. We're always happy to discuss ideas on the [Mailing List][discussion-group].

## Creating a Third Party Package

### Version compatibility

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

## Async Support

*  [adrf](https://github.com/em1208/adrf) - Async support, provides async Views, ViewSets, and Serializers.

### Authentication

* [djangorestframework-digestauth][djangorestframework-digestauth] - Provides Digest Access Authentication support.
* [django-oauth-toolkit][django-oauth-toolkit] - Provides OAuth 2.0 support.
* [djangorestframework-simplejwt][djangorestframework-simplejwt] - Provides JSON Web Token Authentication support.
* [hawkrest][hawkrest] - Provides Hawk HTTP Authorization.
* [djangorestframework-httpsignature][djangorestframework-httpsignature] - Provides an easy to use HTTP Signature Authentication mechanism.
* [djoser][djoser] - Provides a set of views to handle basic actions such as registration, login, logout, password reset and account activation.
* [dj-rest-auth][dj-rest-auth] - Provides a set of REST API endpoints for registration, authentication (including social media authentication), password reset, retrieve and update user details, etc.
* [drf-oidc-auth][drf-oidc-auth] - Implements OpenID Connect token authentication for DRF.
* [drfpasswordless][drfpasswordless] - Adds (Medium, Square Cash inspired) passwordless logins and signups via email and mobile numbers.
* [django-rest-authemail][django-rest-authemail] - Provides a RESTful API for user signup and authentication using email addresses.

### Permissions

* [drf-any-permissions][drf-any-permissions] - Provides alternative permission handling.
* [djangorestframework-composed-permissions][djangorestframework-composed-permissions] - Provides a simple way to define complex permissions.
* [rest_condition][rest-condition] - Another extension for building complex permissions in a simple and convenient way.
* [dry-rest-permissions][dry-rest-permissions] - Provides a simple way to define permissions for individual api actions.
* [drf-access-policy][drf-access-policy] - Declarative and flexible permissions inspired by AWS' IAM policies.
* [drf-psq][drf-psq] - An extension that gives support for having action-based **permission_classes**, **serializer_class**, and **queryset** dependent on permission-based rules.

### Serializers

* [django-rest-framework-mongoengine][django-rest-framework-mongoengine] - Serializer class that supports using MongoDB as the storage layer for Django REST framework.
* [djangorestframework-gis][djangorestframework-gis] - Geographic add-ons
* [djangorestframework-hstore][djangorestframework-hstore] - Serializer class to support django-hstore DictionaryField model field and its schema-mode feature.
* [djangorestframework-jsonapi][djangorestframework-jsonapi] - Provides a parser, renderer, serializers, and other tools to help build an API that is compliant with the jsonapi.org spec.
* [html-json-forms][html-json-forms] - Provides an algorithm and serializer to process HTML JSON Form submissions per the (inactive) spec.
* [django-rest-framework-serializer-extensions][drf-serializer-extensions] -
  Enables black/whitelisting fields, and conditionally expanding child serializers on a per-view/request basis.
* [djangorestframework-queryfields][djangorestframework-queryfields] - Serializer mixin allowing clients to control which fields will be sent in the API response.
* [drf-flex-fields][drf-flex-fields] - Serializer providing dynamic field expansion and sparse field sets via URL parameters.
* [drf-action-serializer][drf-action-serializer] - Serializer providing per-action fields config for use with ViewSets to prevent having to write multiple serializers.
* [djangorestframework-dataclasses][djangorestframework-dataclasses] - Serializer providing automatic field generation for Python dataclasses, like the built-in ModelSerializer does for models.
* [django-restql][django-restql] - Turn your REST API into a GraphQL like API(It allows clients to control which fields will be sent in a response, uses GraphQL like syntax, supports read and write on both flat and nested fields).
* [graphwrap][graphwrap] - Transform your REST API into a fully compliant GraphQL API with just two lines of code. Leverages [Graphene-Django](https://docs.graphene-python.org/projects/django/en/latest/) to dynamically build, at runtime, a GraphQL ObjectType for each view in your API.

### Serializer fields

* [drf-compound-fields][drf-compound-fields] - Provides "compound" serializer fields, such as lists of simple values.
* [drf-extra-fields][drf-extra-fields] - Provides extra serializer fields.
* [django-versatileimagefield][django-versatileimagefield] - Provides a drop-in replacement for Django's stock `ImageField` that makes it easy to serve images in multiple sizes/renditions from a single field. For DRF-specific implementation docs, [click here][django-versatileimagefield-drf-docs].

### Views

* [django-rest-multiple-models][django-rest-multiple-models] - Provides a generic view (and mixin) for sending multiple serialized models and/or querysets via a single API request.
* [drf-typed-views][drf-typed-views] - Use Python type annotations to validate/deserialize request parameters. Inspired by API Star, Hug and FastAPI.
* [rest-framework-actions][rest-framework-actions] - Provides control over each action in ViewSets. Serializers per action, method.

### Routers

* [drf-nested-routers][drf-nested-routers] - Provides routers and relationship fields for working with nested resources.
* [wq.db.rest][wq.db.rest] - Provides an admin-style model registration API with reasonable default URLs and viewsets.

### Parsers

* [djangorestframework-msgpack][djangorestframework-msgpack] - Provides MessagePack renderer and parser support.
* [djangorestframework-jsonapi][djangorestframework-jsonapi] - Provides a parser, renderer, serializers, and other tools to help build an API that is compliant with the jsonapi.org spec.
* [djangorestframework-camel-case][djangorestframework-camel-case] - Provides camel case JSON renderers and parsers.
* [nested-multipart-parser][nested-multipart-parser] - Provides nested parser for http multipart request

### Renderers

* [djangorestframework-csv][djangorestframework-csv] - Provides CSV renderer support.
* [djangorestframework-jsonapi][djangorestframework-jsonapi] - Provides a parser, renderer, serializers, and other tools to help build an API that is compliant with the jsonapi.org spec.
* [drf_ujson2][drf_ujson2] - Implements JSON rendering using the UJSON package.
* [rest-pandas][rest-pandas] - Pandas DataFrame-powered renderers including Excel, CSV, and SVG formats.
* [djangorestframework-rapidjson][djangorestframework-rapidjson] - Provides rapidjson support with parser and renderer.

### Filtering

* [djangorestframework-chain][djangorestframework-chain] - Allows arbitrary chaining of both relations and lookup filters.
* [django-url-filter][django-url-filter] - Allows a safe way to filter data via human-friendly URLs. It is a generic library which is not tied to DRF but it provides easy integration with DRF.
* [drf-url-filter][drf-url-filter] is a simple Django app to apply filters on drf `ModelViewSet`'s `Queryset` in a clean, simple and configurable way. It also supports validations on incoming query params and their values.
* [django-rest-framework-guardian2][django-rest-framework-guardian2] - Provides integration with django-guardian, including the `DjangoObjectPermissionsFilter` previously found in DRF.

### Misc

* [drf-sendables][drf-sendables] - User messages for Django REST Framework
* [cookiecutter-django-rest][cookiecutter-django-rest] - A cookiecutter template that takes care of the setup and configuration so you can focus on making your REST apis awesome.
* [djangorestrelationalhyperlink][djangorestrelationalhyperlink] - A hyperlinked serializer that can can be used to alter relationships via hyperlinks, but otherwise like a hyperlink model serializer.
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
* [django-rest-witchcraft][django-rest-witchcraft] - Provides DRF integration with SQLAlchemy with SQLAlchemy model serializers/viewsets and a bunch of other goodies
* [djangorestframework-mvt][djangorestframework-mvt] - An extension for creating views that serve Postgres data as Map Box Vector Tiles.
* [drf-viewset-profiler][drf-viewset-profiler] - Lib to profile all methods from a viewset line by line.
* [djangorestframework-features][djangorestframework-features] - Advanced schema generation and more based on named features.
* [django-elasticsearch-dsl-drf][django-elasticsearch-dsl-drf] - Integrate Elasticsearch DSL with Django REST framework. Package provides views, serializers, filter backends, pagination and other handy add-ons.
* [django-api-client][django-api-client] - DRF client that groups the Endpoint response, for use in CBVs and FBV as if you were working with Django's Native Models..
* [fast-drf] - A model based library for making API development faster and easier.
* [django-requestlogs] - Providing middleware and other helpers for audit logging for REST framework.
* [drf-standardized-errors][drf-standardized-errors] - DRF exception handler to standardize error responses for all API endpoints.
* [drf-api-action][drf-api-action] - uses the power of DRF also as a library functions

### Customization

* [drf-redesign][drf-redesign] - A project that gives a fresh look to the browse-able API using Bootstrap 5.
* [drf-material][drf-material] - A project that gives a sleek and elegant look to the browsable API using Material Design.

[drf-sendables]: https://github.com/amikrop/drf-sendables
[cite]: http://www.software-ecosystems.com/Software_Ecosystems/Ecosystems.html
[cookiecutter]: https://github.com/jpadilla/cookiecutter-django-rest-framework
[new-repo]: https://github.com/new
[create-a-repo]: https://help.github.com/articles/create-a-repo/
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
[drf-extra-fields]: https://github.com/Hipo/drf-extra-fields
[django-rest-multiple-models]: https://github.com/MattBroach/DjangoRestMultipleModels
[drf-nested-routers]: https://github.com/alanjds/drf-nested-routers
[wq.db.rest]: https://wq.io/docs/about-rest
[djangorestframework-msgpack]: https://github.com/juanriaza/django-rest-framework-msgpack
[djangorestframework-camel-case]: https://github.com/vbabiy/djangorestframework-camel-case
[nested-multipart-parser]: https://github.com/remigermain/nested-multipart-parser
[djangorestframework-csv]: https://github.com/mjumbewu/django-rest-framework-csv
[drf_ujson2]: https://github.com/Amertz08/drf_ujson2
[rest-pandas]: https://github.com/wq/django-rest-pandas
[djangorestframework-rapidjson]: https://github.com/allisson/django-rest-framework-rapidjson
[djangorestframework-chain]: https://github.com/philipn/django-rest-framework-chain
[djangorestrelationalhyperlink]: https://github.com/fredkingham/django_rest_model_hyperlink_serializers_project
[django-rest-framework-proxy]: https://github.com/eofs/django-rest-framework-proxy
[gaiarestframework]: https://github.com/AppsFuel/gaiarestframework
[drf-extensions]: https://github.com/chibisov/drf-extensions
[ember-django-adapter]: https://github.com/dustinfarris/ember-django-adapter
[dj-rest-auth]: https://github.com/iMerica/dj-rest-auth
[django-versatileimagefield]: https://github.com/WGBH/django-versatileimagefield
[django-versatileimagefield-drf-docs]:https://django-versatileimagefield.readthedocs.io/en/latest/drf_integration.html
[drf-tracking]: https://github.com/aschn/drf-tracking
[django-rest-framework-braces]: https://github.com/dealertrack/django-rest-framework-braces
[dry-rest-permissions]: https://github.com/FJNR-inc/dry-rest-permissions
[django-url-filter]: https://github.com/miki725/django-url-filter
[drf-url-filter]: https://github.com/manjitkumar/drf-url-filters
[cookiecutter-django-rest]: https://github.com/agconti/cookiecutter-django-rest
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
[django-rest-witchcraft]: https://github.com/shosca/django-rest-witchcraft
[drf-access-policy]: https://github.com/rsinger86/drf-access-policy
[drf-flex-fields]: https://github.com/rsinger86/drf-flex-fields
[drf-typed-views]: https://github.com/rsinger86/drf-typed-views
[drf-action-serializer]: https://github.com/gregschmit/drf-action-serializer
[djangorestframework-dataclasses]: https://github.com/oxan/djangorestframework-dataclasses
[django-restql]: https://github.com/yezyilomo/django-restql
[djangorestframework-mvt]: https://github.com/corteva/djangorestframework-mvt
[django-rest-framework-guardian2]: https://github.com/johnthagen/django-rest-framework-guardian2
[drf-viewset-profiler]: https://github.com/fvlima/drf-viewset-profiler
[djangorestframework-features]: https://github.com/cloudcode-hungary/django-rest-framework-features/
[django-elasticsearch-dsl-drf]: https://github.com/barseghyanartur/django-elasticsearch-dsl-drf
[django-api-client]: https://github.com/rhenter/django-api-client
[drf-psq]: https://github.com/drf-psq/drf-psq
[django-rest-authemail]: https://github.com/celiao/django-rest-authemail
[graphwrap]: https://github.com/PaulGilmartin/graph_wrap
[rest-framework-actions]: https://github.com/AlexisMunera98/rest-framework-actions
[fast-drf]: https://github.com/iashraful/fast-drf
[django-requestlogs]: https://github.com/Raekkeri/django-requestlogs
[drf-standardized-errors]: https://github.com/ghazi-git/drf-standardized-errors
[drf-api-action]: https://github.com/Ori-Roza/drf-api-action
[drf-redesign]: https://github.com/youzarsiph/drf-redesign
[drf-material]: https://github.com/youzarsiph/drf-material
