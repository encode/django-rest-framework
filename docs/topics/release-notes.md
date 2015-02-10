# Release Notes

> Release Early, Release Often
>
> &mdash; Eric S. Raymond, [The Cathedral and the Bazaar][cite].

## Versioning

Minor version numbers (0.0.x) are used for changes that are API compatible.  You should be able to upgrade between minor point releases without any other code changes.

Medium version numbers (0.x.0) may include API changes, in line with the [deprecation policy][deprecation-policy].  You should read the release notes carefully before upgrading between medium point releases.

Major version numbers (x.0.0) are reserved for substantial project milestones.

## Deprecation policy

REST framework releases follow a formal deprecation policy, which is in line with [Django's deprecation policy][django-deprecation-policy].

The timeline for deprecation of a feature present in version 1.0 would work as follows:

* Version 1.1 would remain **fully backwards compatible** with 1.0, but would raise `PendingDeprecationWarning` warnings if you use the feature that are due to be deprecated.  These warnings are **silent by default**, but can be explicitly enabled when you're ready to start migrating any required changes.  For example if you start running your tests using `python -Wd manage.py test`, you'll be warned of any API changes you need to make.

* Version 1.2 would escalate these warnings to `DeprecationWarning`, which is loud by default.

* Version 1.3 would remove the deprecated bits of API entirely.

Note that in line with Django's policy, any parts of the framework not mentioned in the documentation should generally be considered private API, and may be subject to change.

## Upgrading

To upgrade Django REST framework to the latest version, use pip:

    pip install -U djangorestframework

You can determine your currently installed version using `pip freeze`:

    pip freeze | grep djangorestframework

---

## 3.0.x series


### 3.0.5

**Date**: [10th February 2015][3.0.5-milestone].

* Fix a bug where `_closable_objects` breaks pickling. ([#1850][gh1850], [#2492][gh2492])
* Allow non-standard `User` models with `Throttling`. ([#2524][gh2524])
* Support custom `User.db_table` in TokenAuthentication migration. ([#2479][gh2479])
* Fix misleading `AttributeError` tracebacks on `Request` objects. ([#2530][gh2530], [#2108][gh2108])
* `ManyRelatedField.get_value` clearing field on partial update. ([#2475][gh2475])
* Removed '.model' shortcut from code. ([#2486][gh2486])
* Fix `detail_route` and `list_route` mutable argument. ([#2518][gh2518])
* Prefetching the user object when getting the token in `TokenAuthentication`. ([#2519][gh2519])

### 3.0.4

**Date**: [28th January 2015][3.0.4-milestone].

* Django 1.8a1 support. ([#2425][gh2425], [#2446][gh2446], [#2441][gh2441])
* Add `DictField` and support Django 1.8 `HStoreField`. ([#2451][gh2451], [#2106][gh2106])
* Add `UUIDField` and support Django 1.8 `UUIDField`. ([#2448][gh2448], [#2433][gh2433], [#2432][gh2432])
* `BaseRenderer.render` now raises `NotImplementedError`. ([#2434][gh2434])
* Fix timedelta JSON serialization on Python 2.6. ([#2430][gh2430])
* `ResultDict` and `ResultList` now appear as standard dict/list. ([#2421][gh2421])
* Fix visible `HiddenField` in the HTML form of the web browsable API page. ([#2410][gh2410])
* Use `OrderedDict` for `RelatedField.choices`. ([#2408][gh2408])
* Fix ident format when using `HTTP_X_FORWARDED_FOR`. ([#2401][gh2401])
* Fix invalid key with memcached while using throttling. ([#2400][gh2400])
* Fix `FileUploadParser` with version 3.x. ([#2399][gh2399])
* Fix the serializer inheritance. ([#2388][gh2388])
* Fix caching issues with `ReturnDict`. ([#2360][gh2360])

### 3.0.3

**Date**: [8th January 2015][3.0.3-milestone].

* Fix `MinValueValidator` on `models.DateField`. ([#2369][gh2369])
* Fix serializer missing context when pagination is used. ([#2355][gh2355])
* Namespaced router URLs are now supported by the `DefaultRouter`. ([#2351][gh2351])
* `required=False` allows omission of value for output. ([#2342][gh2342])
* Use textarea input for `models.TextField`. ([#2340][gh2340])
* Use custom `ListSerializer` for pagination if required. ([#2331][gh2331], [#2327][gh2327])
* Better behavior with null and '' for blank HTML fields. ([#2330][gh2330])
* Ensure fields in `exclude` are model fields. ([#2319][gh2319])
* Fix `IntegerField` and `max_length` argument incompatibility. ([#2317][gh2317])
* Fix the YAML encoder for 3.0 serializers. ([#2315][gh2315], [#2283][gh2283])
* Fix the behavior of empty HTML fields. ([#2311][gh2311], [#1101][gh1101])
* Fix Metaclass attribute depth ignoring fields attribute. ([#2287][gh2287])
* Fix `format_suffix_patterns` to work with Django's `i18n_patterns`. ([#2278][gh2278])
* Ability to customize router URLs for custom actions, using `url_path`. ([#2010][gh2010])
* Don't install Django REST Framework as egg. ([#2386][gh2386])

### 3.0.2

**Date**: [17th December 2014][3.0.2-milestone].

* Ensure `request.user` is made available to response middleware. ([#2155][gh2155])
* `Client.logout()` also cancels any existing `force_authenticate`. ([#2218][gh2218], [#2259][gh2259])
* Extra assertions and better checks to preventing incorrect serializer API use. ([#2228][gh2228], [#2234][gh2234], [#2262][gh2262], [#2263][gh2263], [#2266][gh2266], [#2267][gh2267], [#2289][gh2289], [#2291][gh2291])
* Fixed `min_length` message for `CharField`. ([#2255][gh2255])
* Fix `UnicodeDecodeError`, which can occur on serializer `repr`.  ([#2270][gh2270], [#2279][gh2279])
* Fix empty HTML values when a default is provided. ([#2280][gh2280], [#2294][gh2294])
* Fix `SlugRelatedField` raising `UnicodeEncodeError` when used as a multiple choice input. ([#2290][gh2290])

### 3.0.1

**Date**: [11th December 2014][3.0.1-milestone].

* More helpful error message when the default Serializer `create()` fails. ([#2013][gh2013])
* Raise error when attempting to save serializer if data is not valid. ([#2098][gh2098])
* Fix `FileUploadParser` breaks with empty file names and multiple upload handlers. ([#2109][gh2109])
* Improve `BindingDict` to support standard dict-functions. ([#2135][gh2135], [#2163][gh2163])
* Add `validate()` to `ListSerializer`. ([#2168][gh2168], [#2225][gh2225], [#2232][gh2232])
* Fix JSONP renderer failing to escape some characters. ([#2169][gh2169], [#2195][gh2195])
* Add missing default style for `FileField`. ([#2172][gh2172])
* Actions are required when calling `ViewSet.as_view()`. ([#2175][gh2175])
* Add `allow_blank` to `ChoiceField`. ([#2184][gh2184], [#2239][gh2239])
* Cosmetic fixes in the HTML renderer. ([#2187][gh2187])
* Raise error if `fields` on serializer is not a list of strings. ([#2193][gh2193], [#2213][gh2213])
* Improve checks for nested creates and updates. ([#2194][gh2194], [#2196][gh2196])
* `validated_attrs` argument renamed to `validated_data` in `Serializer` `create()`/`update()`. ([#2197][gh2197])
* Remove deprecated code to reflect the dropped Django versions. ([#2200][gh2200])
* Better serializer errors for nested writes. ([#2202][gh2202], [#2215][gh2215])
* Fix pagination and custom permissions incompatibility. ([#2205][gh2205])
* Raise error if `fields` on serializer is not a list of strings. ([#2213][gh2213])
* Add missing translation markers for relational fields. ([#2231][gh2231])
* Improve field lookup behavior for dicts/mappings. ([#2244][gh2244], [#2243][gh2243])
* Optimized hyperlinked PK. ([#2242][gh2242])

### 3.0.0

**Date**: 1st December 2014

For full details see the [3.0 release announcement](3.0-announcement.md).

---

## 2.4.x series

### 2.4.4

**Date**: [3rd November 2014](https://github.com/tomchristie/django-rest-framework/issues?q=milestone%3A%222.4.4+Release%22+).

* **Security fix**: Escape URLs when replacing `format=` query parameter, as used in dropdown on `GET` button in browsable API to allow explicit selection of JSON vs HTML output.
* Maintain ordering of URLs in API root view for `DefaultRouter`.
* Fix `follow=True` in `APIRequestFactory`
* Resolve issue with invalid `read_only=True`, `required=True` fields being automatically generated by `ModelSerializer` in some cases.
* Resolve issue with `OPTIONS` requests returning incorrect information for views using `get_serializer_class` to dynamically determine serializer based on request method. 

### 2.4.3

**Date**: [19th September 2014](https://github.com/tomchristie/django-rest-framework/issues?q=milestone%3A%222.4.3+Release%22+).

* Support translatable view docstrings being displayed in the browsable API.
* Support [encoded `filename*`][rfc-6266] in raw file uploads with `FileUploadParser`.
* Allow routers to support viewsets that don't include any list routes or that don't include any detail routes.
* Don't render an empty login control in browsable API if `login` view is not included.
* CSRF exemption performed in `.as_view()` to prevent accidental omission if overriding `.dispatch()`.
* Login on browsable API now displays validation errors.
* Bugfix: Fix migration in `authtoken` application.
* Bugfix: Allow selection of integer keys in nested choices.
* Bugfix: Return `None` instead of `'None'` in `CharField` with `allow_none=True`.
* Bugfix: Ensure custom model fields map to equivelent serializer fields more reliably.
* Bugfix: `DjangoFilterBackend` no longer quietly changes queryset ordering.

### 2.4.2

**Date**: [3rd September 2014](https://github.com/tomchristie/django-rest-framework/issues?q=milestone%3A%222.4.2+Release%22+).

* Bugfix: Fix broken pagination for 2.4.x series.

### 2.4.1

**Date**: [1st September 2014](https://github.com/tomchristie/django-rest-framework/issues?q=milestone%3A%222.4.1+Release%22+).

* Bugfix: Fix broken login template for browsable API.

### 2.4.0

**Date**: [29th August 2014](https://github.com/tomchristie/django-rest-framework/issues?q=milestone%3A%222.4.0+Release%22+).

**Django version requirements**: The lowest supported version of Django is now 1.4.2.

**South version requirements**: This note applies to any users using the optional `authtoken` application, which includes an associated database migration. You must now *either* upgrade your `south` package to version 1.0, *or* instead use the built-in migration support available with Django 1.7.

* Added compatibility with Django 1.7's database migration support.
* New test runner, using `py.test`.
* Deprecated `.model` view attribute in favor of explicit `.queryset` and `.serializer_class` attributes. The `DEFAULT_MODEL_SERIALIZER_CLASS` setting is also deprecated.
* `@detail_route` and `@list_route` decorators replace `@action` and `@link`.
* Support customizable view name and description functions, using the `VIEW_NAME_FUNCTION` and `VIEW_DESCRIPTION_FUNCTION` settings.
* Added `NUM_PROXIES` setting for smarter client IP identification.
* Added `MAX_PAGINATE_BY` setting and `max_paginate_by` generic view attribute.
* Added `Retry-After` header to throttled responses, as per [RFC 6585](http://tools.ietf.org/html/rfc6585). This should now be used in preference to the custom `X-Trottle-Wait-Seconds` header which will be fully deprecated in 3.0.
* Added `cache` attribute to throttles to allow overriding of default cache.
* Added `lookup_value_regex` attribute to routers, to allow the URL argument matching to be constrainted by the user.
* Added `allow_none` option to `CharField`.
* Support Django's standard `status_code` class attribute on responses.
* More intuitive behavior on the test client, as `client.logout()` now also removes any credentials that have been set.
* Bugfix: `?page_size=0` query parameter now falls back to default page size for view, instead of always turning pagination off.
* Bugfix: Always uppercase `X-Http-Method-Override` methods.
* Bugfix: Copy `filter_backends` list before returning it, in order to prevent view code from mutating the class attribute itself.
* Bugfix: Set the `.action` attribute on viewsets when introspected by `OPTIONS` for testing permissions on the view.
* Bugfix: Ensure `ValueError` raised during deserialization results in a error list rather than a single error. This is now consistent with other validation errors.
* Bugfix: Fix `cache_format` typo on throttle classes, was `"throtte_%(scope)s_%(ident)s"`. Note that this will invalidate existing throttle caches.

---

## 2.3.x series

### 2.3.14

**Date**: 12th June 2014

* **Security fix**: Escape request path when it is include as part of the login and logout links in the browsable API.
* `help_text` and `verbose_name` automatically set for related fields on `ModelSerializer`.
* Fix nested serializers linked through a backward foreign key relation.
* Fix bad links for the `BrowsableAPIRenderer` with `YAMLRenderer`.
* Add `UnicodeYAMLRenderer` that extends `YAMLRenderer` with unicode.
* Fix `parse_header` argument convertion.
* Fix mediatype detection under Python 3.
* Web browsable API now offers blank option on dropdown when the field is not required.
* `APIException` representation improved for logging purposes.
* Allow source="*" within nested serializers.
* Better support for custom oauth2 provider backends.
* Fix field validation if it's optional and has no value.
* Add `SEARCH_PARAM` and `ORDERING_PARAM`.
* Fix `APIRequestFactory` to support arguments within the url string for GET.
* Allow three transport modes for access tokens when accessing a protected resource.
* Fix `QueryDict` encoding on request objects.
* Ensure throttle keys do not contain spaces, as those are invalid if using `memcached`.
* Support `blank_display_value` on `ChoiceField`.

### 2.3.13

**Date**: 6th March 2014

* Django 1.7 Support.
* Fix `default` argument when used with serializer relation fields.
* Display the media type of the content that is being displayed in the browsable API, rather than 'text/html'.
* Bugfix for `urlize` template failure when URL regex is matched, but value does not `urlparse`.
* Use `urandom` for token generation.
* Only use `Vary: Accept` when more than one renderer exists.

### 2.3.12

**Date**: 15th January 2014

* **Security fix**: `OrderingField` now only allows ordering on readable serializer fields, or on fields explicitly specified using `ordering_fields`. This prevents users being able to order by fields that are not visible in the API, and exploiting the ordering of sensitive data such as password hashes.
* Bugfix: `write_only = True` fields now display in the browsable API.

### 2.3.11

**Date**: 14th January 2014

* Added `write_only` serializer field argument.
* Added `write_only_fields` option to `ModelSerializer` classes.
* JSON renderer now deals with objects that implement a dict-like interface.
* Fix compatiblity with newer versions of `django-oauth-plus`.
* Bugfix: Refine behavior that calls model manager `all()` across nested serializer relationships, preventing erronous behavior with some non-ORM objects, and preventing unnecessary queryset re-evaluations.
* Bugfix: Allow defaults on BooleanFields to be properly honored when values are not supplied.
* Bugfix: Prevent double-escaping of non-latin1 URL query params when appending `format=json` params.

### 2.3.10

**Date**: 6th December 2013

* Add in choices information for ChoiceFields in response to `OPTIONS` requests.
* Added `pre_delete()` and `post_delete()` method hooks.
* Added status code category helper functions.
* Bugfix: Partial updates which erronously set a related field to `None` now correctly fail validation instead of raising an exception.
* Bugfix: Responses without any content no longer include an HTTP `'Content-Type'` header.
* Bugfix: Correctly handle validation errors in PUT-as-create case, responding with 400.

### 2.3.9

**Date**: 15th November 2013

* Fix Django 1.6 exception API compatibility issue caused by `ValidationError`.
* Include errors in HTML forms in browsable API.
* Added JSON renderer support for numpy scalars.
* Added `transform_<fieldname>` hooks on serializers for easily modifying field output.
* Added `get_context` hook in `BrowsableAPIRenderer`.
* Allow serializers to be passed `files` but no `data`.
* `HTMLFormRenderer` now renders serializers directly to HTML without needing to create an intermediate form object.
* Added `get_filter_backends` hook.
* Added queryset aggregates to allowed fields in `OrderingFilter`.
* Bugfix: Fix decimal suppoprt with `YAMLRenderer`.
* Bugfix: Fix submission of unicode in browsable API through raw data form.

### 2.3.8

**Date**: 11th September 2013

* Added `DjangoObjectPermissions`, and `DjangoObjectPermissionsFilter`.
* Support customizable exception handling, using the `EXCEPTION_HANDLER` setting.
* Support customizable view name and description functions, using the `VIEW_NAME_FUNCTION` and `VIEW_DESCRIPTION_FUNCTION` settings.
* Added `MAX_PAGINATE_BY` setting and `max_paginate_by` generic view attribute.
* Added `cache` attribute to throttles to allow overriding of default cache.
* 'Raw data' tab in browsable API now contains pre-populated data.
* 'Raw data' and 'HTML form' tab preference in browsable API now saved between page views.
* Bugfix: `required=True` argument fixed for boolean serializer fields.
* Bugfix: `client.force_authenticate(None)` should also clear session info if it exists.
* Bugfix: Client sending empty string instead of file now clears `FileField`.
* Bugfix: Empty values on ChoiceFields with `required=False` now consistently return `None`.
* Bugfix: Clients setting `page_size=0` now simply returns the default page size, instead of disabling pagination. [*]

---

[*] Note that the change in `page_size=0` behaviour fixes what is considered to be a bug in how clients can effect the pagination size.  However if you were relying on this behavior you will need to add the following mixin to your list views in order to preserve the existing behavior.

    class DisablePaginationMixin(object):
        def get_paginate_by(self, queryset=None):
            if self.request.QUERY_PARAMS[self.paginate_by_param] == '0':
                return None
            return super(DisablePaginationMixin, self).get_paginate_by(queryset)

---

### 2.3.7

**Date**: 16th August 2013

* Added `APITestClient`, `APIRequestFactory` and `APITestCase` etc...
* Refactor `SessionAuthentication` to allow esier override for CSRF exemption.
* Remove 'Hold down "Control" message from help_text' widget messaging when not appropriate.
* Added admin configuration for auth tokens.
* Bugfix: `AnonRateThrottle` fixed to not throttle authenticated users.
* Bugfix: Don't set `X-Throttle-Wait-Seconds` when throttle does not have `wait` value.
* Bugfix: Fixed `PATCH` button title in browsable API.
* Bugfix: Fix issue with OAuth2 provider naive datetimes.

### 2.3.6

**Date**: 27th June 2013

* Added `trailing_slash` option to routers.
* Include support for `HttpStreamingResponse`.
* Support wider range of default serializer validation when used with custom model fields.
* UTF-8 Support for browsable API descriptions.
* OAuth2 provider uses timezone aware datetimes when supported.
* Bugfix: Return error correctly when OAuth non-existent consumer occurs.
* Bugfix: Allow `FileUploadParser` to correctly filename if provided as URL kwarg.
* Bugfix: Fix `ScopedRateThrottle`.

### 2.3.5

**Date**: 3rd June 2013

* Added `get_url` hook to `HyperlinkedIdentityField`.
* Serializer field `default` argument may be a callable.
* `@action` decorator now accepts a `methods` argument.
* Bugfix: `request.user` should be still be accessible in renderer context if authentication fails.
* Bugfix: The `lookup_field` option on `HyperlinkedIdentityField` should apply by default to the url field on the serializer.
* Bugfix: `HyperlinkedIdentityField` should continue to support `pk_url_kwarg`, `slug_url_kwarg`, `slug_field`, in a pending deprecation state.
* Bugfix: Ensure we always return 404 instead of 500 if a lookup field cannot be converted to the correct lookup type.  (Eg non-numeric `AutoInteger` pk lookup)

### 2.3.4

**Date**: 24th May 2013

* Serializer fields now support `label` and `help_text`.
* Added `UnicodeJSONRenderer`.
* `OPTIONS` requests now return metadata about fields for `POST` and `PUT` requests.
* Bugfix: `charset` now properly included in `Content-Type` of responses.
* Bugfix: Blank choice now added in browsable API on nullable relationships.
* Bugfix: Many to many relationships with `through` tables are now read-only.
* Bugfix: Serializer fields now respect model field args such as `max_length`.
* Bugfix: SlugField now performs slug validation.
* Bugfix: Lazy-translatable strings now properly serialized.
* Bugfix: Browsable API now supports bootswatch styles properly.
* Bugfix: HyperlinkedIdentityField now uses `lookup_field` kwarg.

**Note**: Responses now correctly include an appropriate charset on the `Content-Type` header.  For example: `application/json; charset=utf-8`.  If you have tests that check the content type of responses, you may need to update these accordingly.

### 2.3.3

**Date**: 16th May 2013

* Added SearchFilter
* Added OrderingFilter
* Added GenericViewSet
* Bugfix: Multiple `@action` and `@link` methods now allowed on viewsets.
* Bugfix: Fix API Root view issue with DjangoModelPermissions

### 2.3.2

**Date**: 8th May 2013

* Bugfix: Fix `TIME_FORMAT`, `DATETIME_FORMAT` and `DATE_FORMAT` settings.
* Bugfix: Fix `DjangoFilterBackend` issue, failing when used on view with queryset attribute.

### 2.3.1

**Date**: 7th May 2013

* Bugfix: Fix breadcrumb rendering issue.

### 2.3.0

**Date**: 7th May 2013

* ViewSets and Routers.
* ModelSerializers support reverse relations in 'fields' option.
* HyperLinkedModelSerializers support 'id' field in 'fields' option.
* Cleaner generic views.
* Support for multiple filter classes.
* FileUploadParser support for raw file uploads.
* DecimalField support.
* Made Login template easier to restyle.
* Bugfix: Fix issue with depth>1 on ModelSerializer.

**Note**: See the [2.3 announcement][2.3-announcement] for full details.

---

## 2.2.x series

### 2.2.7

**Date**: 17th April 2013

* Loud failure when view does not return a `Response` or `HttpResponse`.
* Bugfix: Fix for Django 1.3 compatibility.
* Bugfix: Allow overridden `get_object()` to work correctly.

### 2.2.6

**Date**: 4th April 2013

* OAuth2 authentication no longer requires unnecessary URL parameters in addition to the token.
* URL hyperlinking in browsable API now handles more cases correctly.
* Long HTTP headers in browsable API are broken in multiple lines when possible.
* Bugfix: Fix regression with DjangoFilterBackend not worthing correctly with single object views.
* Bugfix: OAuth should fail hard when invalid token used.
* Bugfix: Fix serializer potentially returning `None` object for models that define `__bool__` or `__len__`.

### 2.2.5

**Date**: 26th March 2013

* Serializer support for bulk create and bulk update operations.
* Regression fix: Date and time fields return date/time objects by default.  Fixes regressions caused by 2.2.2.  See [#743][743] for more details.
* Bugfix: Fix 500 error is OAuth not attempted with OAuthAuthentication class installed.
* `Serializer.save()` now supports arbitrary keyword args which are passed through to the object `.save()` method.  Mixins use `force_insert` and `force_update` where appropriate, resulting in one less database query.

### 2.2.4

**Date**: 13th March 2013

* OAuth 2 support.
* OAuth 1.0a support.
* Support X-HTTP-Method-Override header.
* Filtering backends are now applied to the querysets for object lookups as well as lists.  (Eg you can use a filtering backend to control which objects should 404)
* Deal with error data nicely when deserializing lists of objects.
* Extra override hook to configure `DjangoModelPermissions` for unauthenticated users.
* Bugfix: Fix regression which caused extra database query on paginated list views.
* Bugfix: Fix pk relationship bug for some types of 1-to-1 relations.
* Bugfix: Workaround for Django bug causing case where `Authtoken` could be registered for cascade delete from `User` even if not installed.

### 2.2.3

**Date**: 7th March 2013

* Bugfix: Fix None values for for `DateField`, `DateTimeField` and `TimeField`.

### 2.2.2

**Date**: 6th March 2013

* Support for custom input and output formats for `DateField`, `DateTimeField` and `TimeField`.
* Cleanup: Request authentication is no longer lazily evaluated, instead authentication is always run, which results in more consistent, obvious behavior.  Eg. Supplying bad auth credentials will now always return an error response, even if no permissions are set on the view.
* Bugfix for serializer data being uncacheable with pickle protocol 0.
* Bugfixes for model field validation edge-cases.
* Bugfix for authtoken migration while using a custom user model and south.

### 2.2.1

**Date**: 22nd Feb 2013

* Security fix: Use `defusedxml` package to address XML parsing vulnerabilities.
* Raw data tab added to browsable API.  (Eg. Allow for JSON input.)
* Added TimeField.
* Serializer fields can be mapped to any method that takes no args, or only takes kwargs which have defaults.
* Unicode support for view names/descriptions in browsable API.
* Bugfix: request.DATA should return an empty `QueryDict` with no data, not `None`.
* Bugfix: Remove unneeded field validation, which caused extra queries.

**Security note**: Following the [disclosure of security vulnerabilities][defusedxml-announce] in Python's XML parsing libraries, use of the `XMLParser` class now requires the `defusedxml` package to be installed.

The security vulnerabilities only affect APIs which use the `XMLParser` class, by enabling it in any views, or by having it set in the `DEFAULT_PARSER_CLASSES` setting.  Note that the `XMLParser` class is not enabled by default, so this change should affect a minority of users.

### 2.2.0

**Date**: 13th Feb 2013

* Python 3 support.
* Added a `post_save()` hook to the generic views.
* Allow serializers to handle dicts as well as objects.
* Deprecate `ManyRelatedField()` syntax in favor of `RelatedField(many=True)`
* Deprecate `null=True` on relations in favor of `required=False`.
* Deprecate `blank=True` on CharFields, just use `required=False`.
* Deprecate optional `obj` argument in permissions checks in favor of `has_object_permission`.
* Deprecate implicit hyperlinked relations behavior.
* Bugfix: Fix broken DjangoModelPermissions.
* Bugfix: Allow serializer output to be cached.
* Bugfix: Fix styling on browsable API login.
* Bugfix: Fix issue with deserializing empty to-many relations.
* Bugfix: Ensure model field validation is still applied for ModelSerializer subclasses with an custom `.restore_object()` method.

**Note**: See the [2.2 announcement][2.2-announcement] for full details.

---

## 2.1.x series

### 2.1.17

**Date**: 26th Jan 2013

* Support proper 401 Unauthorized responses where appropriate, instead of always using 403 Forbidden.
* Support json encoding of timedelta objects.
* `format_suffix_patterns()` now supports `include` style URL patterns.
* Bugfix: Fix issues with custom pagination serializers.
* Bugfix: Nested serializers now accept `source='*'` argument.
* Bugfix: Return proper validation errors when incorrect types supplied for relational fields.
* Bugfix: Support nullable FKs with `SlugRelatedField`.
* Bugfix: Don't call custom validation methods if the field has an error.

**Note**: If the primary authentication class is `TokenAuthentication` or `BasicAuthentication`, a view will now correctly return 401 responses to unauthenticated access, with an appropriate `WWW-Authenticate` header, instead of 403 responses.

### 2.1.16

**Date**: 14th Jan 2013

* Deprecate `django.utils.simplejson` in favor of Python 2.6's built-in json module.
* Bugfix: `auto_now`, `auto_now_add` and other `editable=False` fields now default to read-only.
* Bugfix: PK fields now only default to read-only if they are an AutoField or if `editable=False`.
* Bugfix: Validation errors instead of exceptions when serializers receive incorrect types.
* Bugfix: Validation errors instead of exceptions when related fields receive incorrect types.
* Bugfix: Handle ObjectDoesNotExist exception when serializing null reverse one-to-one

**Note**: Prior to 2.1.16, The Decimals would render in JSON using floating point if `simplejson` was installed, but otherwise render using string notation.  Now that use of `simplejson` has been deprecated, Decimals will consistently render using string notation.  See [ticket 582](ticket-582) for more details.

### 2.1.15

**Date**: 3rd Jan 2013

* Added `PATCH` support.
* Added `RetrieveUpdateAPIView`.
* Remove unused internal `save_m2m` flag on `ModelSerializer.save()`.
* Tweak behavior of hyperlinked fields with an explicit format suffix.
* Relation changes are now persisted in `.save()` instead of in `.restore_object()`.
* Bugfix: Fix issue with FileField raising exception instead of validation error when files=None.
* Bugfix: Partial updates should not set default values if field is not included.

### 2.1.14

**Date**: 31st Dec 2012

* Bugfix: ModelSerializers now include reverse FK fields on creation.
* Bugfix: Model fields with `blank=True` are now `required=False` by default.
* Bugfix: Nested serializers now support nullable relationships.

**Note**: From 2.1.14 onwards, relational fields move out of the `fields.py` module and into the new `relations.py` module, in order to separate them from regular data type fields, such as `CharField` and `IntegerField`.

This change will not affect user code, so long as it's following the recommended import style of `from rest_framework import serializers` and referring to fields using the style `serializers.PrimaryKeyRelatedField`.


### 2.1.13

**Date**: 28th Dec 2012

* Support configurable `STATICFILES_STORAGE` storage.
* Bugfix: Related fields now respect the required flag, and may be required=False.

### 2.1.12

**Date**: 21st Dec 2012

* Bugfix: Fix bug that could occur using ChoiceField.
* Bugfix: Fix exception in browsable API on DELETE.
* Bugfix: Fix issue where pk was was being set to a string if set by URL kwarg.

### 2.1.11

**Date**: 17th Dec 2012

* Bugfix: Fix issue with M2M fields in browsable API.

### 2.1.10

**Date**: 17th Dec 2012

* Bugfix: Ensure read-only fields don't have model validation applied.
* Bugfix: Fix hyperlinked fields in paginated results.

### 2.1.9

**Date**: 11th Dec 2012

* Bugfix: Fix broken nested serialization.
* Bugfix: Fix `Meta.fields` only working as tuple not as list.
* Bugfix: Edge case if unnecessarily specifying `required=False` on read only field.

### 2.1.8

**Date**: 8th Dec 2012

* Fix for creating nullable Foreign Keys with `''` as well as `None`.
* Added `null=<bool>` related field option.

### 2.1.7

**Date**: 7th Dec 2012

* Serializers now properly support nullable Foreign Keys.
* Serializer validation now includes model field validation, such as uniqueness constraints.
* Support 'true' and 'false' string values for BooleanField.
* Added pickle support for serialized data.
* Support `source='dotted.notation'` style for nested serializers.
* Make `Request.user` settable.
* Bugfix: Fix `RegexField` to work with `BrowsableAPIRenderer`.

### 2.1.6

**Date**: 23rd Nov 2012

* Bugfix: Unfix DjangoModelPermissions.  (I am a doofus.)

### 2.1.5

**Date**: 23rd Nov 2012

* Bugfix: Fix DjangoModelPermissions.

### 2.1.4

**Date**: 22nd Nov 2012

* Support for partial updates with serializers.
* Added `RegexField`.
* Added `SerializerMethodField`.
* Serializer performance improvements.
* Added `obtain_token_view` to get tokens when using `TokenAuthentication`.
* Bugfix: Django 1.5 configurable user support for `TokenAuthentication`.

### 2.1.3

**Date**: 16th Nov 2012

* Added `FileField` and `ImageField`.  For use with `MultiPartParser`.
* Added `URLField` and `SlugField`.
* Support for `read_only_fields` on `ModelSerializer` classes.
* Support for clients overriding the pagination page sizes.  Use the `PAGINATE_BY_PARAM` setting or set the `paginate_by_param` attribute on a generic view.
* 201 Responses now return a 'Location' header.
* Bugfix: Serializer fields now respect `max_length`.

### 2.1.2

**Date**: 9th Nov 2012

* **Filtering support.**
* Bugfix: Support creation of objects with reverse M2M relations.

### 2.1.1

**Date**: 7th Nov 2012

* Support use of HTML exception templates.  Eg. `403.html`
* Hyperlinked fields take optional `slug_field`, `slug_url_kwarg` and `pk_url_kwarg` arguments.
* Bugfix: Deal with optional trailing slashes properly when generating breadcrumbs.
* Bugfix: Make textareas same width as other fields in browsable API.
* Private API change: `.get_serializer` now uses same `instance` and `data` ordering as serializer initialization.

### 2.1.0

**Date**: 5th Nov 2012

* **Serializer `instance` and `data` keyword args have their position swapped.**
* `queryset` argument is now optional on writable model fields.
* Hyperlinked related fields optionally take `slug_field` and `slug_url_kwarg` arguments.
* Support Django's cache framework.
* Minor field improvements. (Don't stringify dicts, more robust many-pk fields.)
* Bugfix: Support choice field in Browsable API.
* Bugfix: Related fields with `read_only=True` do not require a `queryset` argument.

**API-incompatible changes**: Please read [this thread][2.1.0-notes] regarding the `instance` and `data` keyword args before updating to 2.1.0.

---

## 2.0.x series

### 2.0.2

**Date**: 2nd Nov 2012

* Fix issues with pk related fields in the browsable API.

### 2.0.1

**Date**: 1st Nov 2012

* Add support for relational fields in the browsable API.
* Added SlugRelatedField and ManySlugRelatedField.
* If PUT creates an instance return '201 Created', instead of '200 OK'.

### 2.0.0

**Date**: 30th Oct 2012

* **Fix all of the things.**  (Well, almost.)
* For more information please see the [2.0 announcement][announcement].

For older release notes, [please see the GitHub repo](old-release-notes).

[cite]: http://www.catb.org/~esr/writings/cathedral-bazaar/cathedral-bazaar/ar01s04.html
[deprecation-policy]: #deprecation-policy
[django-deprecation-policy]: https://docs.djangoproject.com/en/dev/internals/release-process/#internal-release-deprecation-policy
[defusedxml-announce]: http://blog.python.org/2013/02/announcing-defusedxml-fixes-for-xml.html
[2.2-announcement]: 2.2-announcement.md
[2.3-announcement]: 2.3-announcement.md
[743]: https://github.com/tomchristie/django-rest-framework/pull/743
[staticfiles14]: https://docs.djangoproject.com/en/1.4/howto/static-files/#with-a-template-tag
[staticfiles13]: https://docs.djangoproject.com/en/1.3/howto/static-files/#with-a-template-tag
[2.1.0-notes]: https://groups.google.com/d/topic/django-rest-framework/Vv2M0CMY9bg/discussion
[announcement]: rest-framework-2-announcement.md
[ticket-582]: https://github.com/tomchristie/django-rest-framework/issues/582
[rfc-6266]: http://tools.ietf.org/html/rfc6266#section-4.3
[old-release-notes]: https://github.com/tomchristie/django-rest-framework/blob/2.4.4/docs/topics/release-notes.md#04x-series

[3.0.1-milestone]: https://github.com/tomchristie/django-rest-framework/issues?q=milestone%3A%223.0.1+Release%22
[3.0.2-milestone]: https://github.com/tomchristie/django-rest-framework/issues?q=milestone%3A%223.0.2+Release%22
[3.0.3-milestone]: https://github.com/tomchristie/django-rest-framework/issues?q=milestone%3A%223.0.3+Release%22
[3.0.4-milestone]: https://github.com/tomchristie/django-rest-framework/issues?q=milestone%3A%223.0.4+Release%22
[3.0.5-milestone]: https://github.com/tomchristie/django-rest-framework/issues?q=milestone%3A%223.0.5+Release%22

<!-- 3.0.1 -->
[gh2013]: https://github.com/tomchristie/django-rest-framework/issues/2013
[gh2098]: https://github.com/tomchristie/django-rest-framework/issues/2098
[gh2109]: https://github.com/tomchristie/django-rest-framework/issues/2109
[gh2135]: https://github.com/tomchristie/django-rest-framework/issues/2135
[gh2163]: https://github.com/tomchristie/django-rest-framework/issues/2163
[gh2168]: https://github.com/tomchristie/django-rest-framework/issues/2168
[gh2169]: https://github.com/tomchristie/django-rest-framework/issues/2169
[gh2172]: https://github.com/tomchristie/django-rest-framework/issues/2172
[gh2175]: https://github.com/tomchristie/django-rest-framework/issues/2175
[gh2184]: https://github.com/tomchristie/django-rest-framework/issues/2184
[gh2187]: https://github.com/tomchristie/django-rest-framework/issues/2187
[gh2193]: https://github.com/tomchristie/django-rest-framework/issues/2193
[gh2194]: https://github.com/tomchristie/django-rest-framework/issues/2194
[gh2195]: https://github.com/tomchristie/django-rest-framework/issues/2195
[gh2196]: https://github.com/tomchristie/django-rest-framework/issues/2196
[gh2197]: https://github.com/tomchristie/django-rest-framework/issues/2197
[gh2200]: https://github.com/tomchristie/django-rest-framework/issues/2200
[gh2202]: https://github.com/tomchristie/django-rest-framework/issues/2202
[gh2205]: https://github.com/tomchristie/django-rest-framework/issues/2205
[gh2213]: https://github.com/tomchristie/django-rest-framework/issues/2213
[gh2213]: https://github.com/tomchristie/django-rest-framework/issues/2213
[gh2215]: https://github.com/tomchristie/django-rest-framework/issues/2215
[gh2225]: https://github.com/tomchristie/django-rest-framework/issues/2225
[gh2231]: https://github.com/tomchristie/django-rest-framework/issues/2231
[gh2232]: https://github.com/tomchristie/django-rest-framework/issues/2232
[gh2239]: https://github.com/tomchristie/django-rest-framework/issues/2239
[gh2242]: https://github.com/tomchristie/django-rest-framework/issues/2242
[gh2243]: https://github.com/tomchristie/django-rest-framework/issues/2243
[gh2244]: https://github.com/tomchristie/django-rest-framework/issues/2244
<!-- 3.0.2 -->
[gh2155]: https://github.com/tomchristie/django-rest-framework/issues/2155
[gh2218]: https://github.com/tomchristie/django-rest-framework/issues/2218
[gh2228]: https://github.com/tomchristie/django-rest-framework/issues/2228
[gh2234]: https://github.com/tomchristie/django-rest-framework/issues/2234
[gh2255]: https://github.com/tomchristie/django-rest-framework/issues/2255
[gh2259]: https://github.com/tomchristie/django-rest-framework/issues/2259
[gh2262]: https://github.com/tomchristie/django-rest-framework/issues/2262
[gh2263]: https://github.com/tomchristie/django-rest-framework/issues/2263
[gh2266]: https://github.com/tomchristie/django-rest-framework/issues/2266
[gh2267]: https://github.com/tomchristie/django-rest-framework/issues/2267
[gh2270]: https://github.com/tomchristie/django-rest-framework/issues/2270
[gh2279]: https://github.com/tomchristie/django-rest-framework/issues/2279
[gh2280]: https://github.com/tomchristie/django-rest-framework/issues/2280
[gh2289]: https://github.com/tomchristie/django-rest-framework/issues/2289
[gh2290]: https://github.com/tomchristie/django-rest-framework/issues/2290
[gh2291]: https://github.com/tomchristie/django-rest-framework/issues/2291
[gh2294]: https://github.com/tomchristie/django-rest-framework/issues/2294
<!-- 3.0.3 -->
[gh1101]: https://github.com/tomchristie/django-rest-framework/issues/1101
[gh2010]: https://github.com/tomchristie/django-rest-framework/issues/2010
[gh2278]: https://github.com/tomchristie/django-rest-framework/issues/2278
[gh2283]: https://github.com/tomchristie/django-rest-framework/issues/2283
[gh2287]: https://github.com/tomchristie/django-rest-framework/issues/2287
[gh2311]: https://github.com/tomchristie/django-rest-framework/issues/2311
[gh2315]: https://github.com/tomchristie/django-rest-framework/issues/2315
[gh2317]: https://github.com/tomchristie/django-rest-framework/issues/2317
[gh2319]: https://github.com/tomchristie/django-rest-framework/issues/2319
[gh2327]: https://github.com/tomchristie/django-rest-framework/issues/2327
[gh2330]: https://github.com/tomchristie/django-rest-framework/issues/2330
[gh2331]: https://github.com/tomchristie/django-rest-framework/issues/2331
[gh2340]: https://github.com/tomchristie/django-rest-framework/issues/2340
[gh2342]: https://github.com/tomchristie/django-rest-framework/issues/2342
[gh2351]: https://github.com/tomchristie/django-rest-framework/issues/2351
[gh2355]: https://github.com/tomchristie/django-rest-framework/issues/2355
[gh2369]: https://github.com/tomchristie/django-rest-framework/issues/2369
[gh2386]: https://github.com/tomchristie/django-rest-framework/issues/2386
<!-- 3.0.4 -->
[gh2425]: https://github.com/tomchristie/django-rest-framework/issues/2425
[gh2446]: https://github.com/tomchristie/django-rest-framework/issues/2446
[gh2441]: https://github.com/tomchristie/django-rest-framework/issues/2441
[gh2451]: https://github.com/tomchristie/django-rest-framework/issues/2451
[gh2106]: https://github.com/tomchristie/django-rest-framework/issues/2106
[gh2448]: https://github.com/tomchristie/django-rest-framework/issues/2448
[gh2433]: https://github.com/tomchristie/django-rest-framework/issues/2433
[gh2432]: https://github.com/tomchristie/django-rest-framework/issues/2432
[gh2434]: https://github.com/tomchristie/django-rest-framework/issues/2434
[gh2430]: https://github.com/tomchristie/django-rest-framework/issues/2430
[gh2421]: https://github.com/tomchristie/django-rest-framework/issues/2421
[gh2410]: https://github.com/tomchristie/django-rest-framework/issues/2410
[gh2408]: https://github.com/tomchristie/django-rest-framework/issues/2408
[gh2401]: https://github.com/tomchristie/django-rest-framework/issues/2401
[gh2400]: https://github.com/tomchristie/django-rest-framework/issues/2400
[gh2399]: https://github.com/tomchristie/django-rest-framework/issues/2399
[gh2388]: https://github.com/tomchristie/django-rest-framework/issues/2388
[gh2360]: https://github.com/tomchristie/django-rest-framework/issues/2360
<!-- 3.0.5 -->
[gh1850]: https://github.com/tomchristie/django-rest-framework/issues/1850
[gh2108]: https://github.com/tomchristie/django-rest-framework/issues/2108
[gh2475]: https://github.com/tomchristie/django-rest-framework/issues/2475
[gh2479]: https://github.com/tomchristie/django-rest-framework/issues/2479
[gh2486]: https://github.com/tomchristie/django-rest-framework/issues/2486
[gh2492]: https://github.com/tomchristie/django-rest-framework/issues/2492
[gh2518]: https://github.com/tomchristie/django-rest-framework/issues/2518
[gh2519]: https://github.com/tomchristie/django-rest-framework/issues/2519
[gh2524]: https://github.com/tomchristie/django-rest-framework/issues/2524
[gh2530]: https://github.com/tomchristie/django-rest-framework/issues/2530
