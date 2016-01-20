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

## 3.3.x series

### 3.3.2

**Date**: [14th December 2015][3.3.2-milestone].

* `ListField` enforces input is a list. ([#3513][gh3513])
* Fix regression hiding raw data form. ([#3600][gh3600], [#3578][gh3578])
* Fix Python 3.5 compatibility. ([#3534][gh3534], [#3626][gh3626])
* Allow setting a custom Django Paginator in `pagination.PageNumberPagination`. ([#3631][gh3631], [#3684][gh3684])
* Fix relational fields without `to_fields` attribute. ([#3635][gh3635], [#3634][gh3634])
* Fix `template.render` deprecation warnings for Django 1.9. ([#3654][gh3654])
* Sort response headers in browsable API renderer. ([#3655][gh3655])
* Use related_objects api for Django 1.9+. ([#3656][gh3656], [#3252][gh3252])
* Add confirm modal when deleting. ([#3228][gh3228], [#3662][gh3662])
* Reveal previously hidden AttributeErrors and TypeErrors while calling has_[object_]permissions. ([#3668][gh3668])
* Make DRF compatible with multi template engine in Django 1.8. ([#3672][gh3672])
* Update `NestedBoundField` to also handle empty string when rendering its form. ([#3677][gh3677])
* Fix UUID validation to properly catch invalid input types. ([#3687][gh3687], [#3679][gh3679])
* Fix caching issues. ([#3628][gh3628], [#3701][gh3701])
* Fix Admin and API browser for views without a filter_class. ([#3705][gh3705], [#3596][gh3596], [#3597][gh3597])
* Add app_name to rest_framework.urls. ([#3714][gh3714])
* Improve authtoken's views to support url versioning. ([#3718][gh3718], [#3723][gh3723])

### 3.3.1

**Date**: [4th November 2015][3.3.1-milestone].

* Resolve parsing bug when accessing `request.POST` ([#3592][gh3592])
* Correctly deal with `to_field` referring to primary key. ([#3593][gh3593])
* Allow filter HTML to render when no `filter_class` is defined. ([#3560][gh3560])
* Fix admin rendering issues. ([#3564][gh3564], [#3556][gh3556])
* Fix issue with DecimalValidator. ([#3568][gh3568])

### 3.3.0

**Date**: [28th October 2015][3.3.0-milestone].

* HTML controls for filters. ([#3315][gh3315])
* Forms API. ([#3475][gh3475])
* AJAX browsable API. ([#3410][gh3410])
* Added JSONField. ([#3454][gh3454])
* Correctly map `to_field` when creating `ModelSerializer` relational fields. ([#3526][gh3526])
* Include keyword arguments when mapping `FilePathField` to a serializer field. ([#3536][gh3536])
* Map appropriate model `error_messages` on `ModelSerializer` uniqueness constraints. ([#3435][gh3435])
* Include `max_length` constraint for `ModelSerializer` fields mapped from TextField. ([#3509][gh3509])
* Added support for Django 1.9. ([#3450][gh3450], [#3525][gh3525])
* Removed support for Django 1.5 & 1.6. ([#3421][gh3421], [#3429][gh3429])
* Removed 'south' migrations. ([#3495][gh3495])

## 3.2.x series

### 3.2.5

**Date**: [27th October 2015][3.2.5-milestone].

* Escape `username` in optional logout tag. ([#3550][gh3550])

### 3.2.4

**Date**: [21th September 2015][3.2.4-milestone].

* Don't error on missing `ViewSet.search_fields` attribute. ([#3324][gh3324], [#3323][gh3323])
* Fix `allow_empty` not working on serializers with `many=True`. ([#3361][gh3361], [#3364][gh3364])
* Let `DurationField` accepts integers. ([#3359][gh3359])
* Multi-level dictionaries not supported in multipart requests. ([#3314][gh3314])
* Fix `ListField` truncation on HTTP PATCH ([#3415][gh3415], [#2761][gh2761])

### 3.2.3

**Date**: [24th August 2015][3.2.3-milestone].

* Added `html_cutoff` and `html_cutoff_text` for limiting select dropdowns. ([#3313][gh3313])
* Added regex style to `SearchFilter`. ([#3316][gh3316])
* Resolve issues with setting blank HTML fields. ([#3318][gh3318]) ([#3321][gh3321])
* Correctly display existing 'select multiple' values in browsable API forms. ([#3290][gh3290])
* Resolve duplicated validation message for `IPAddressField`. ([#3249[gh3249]) ([#3250][gh3250])
* Fix to ensure admin renderer continues to work when pagination is disabled. ([#3275][gh3275])
* Resolve error with `LimitOffsetPagination` when count=0, offset=0. ([#3303][gh3303])

### 3.2.2

**Date**: [13th August 2015][3.2.2-milestone].

* Add `display_value()` method for use when displaying relational field select inputs. ([#3254][gh3254])
* Fix issue with `BooleanField` checkboxes incorrectly displaying as checked. ([#3258][gh3258])
* Ensure empty checkboxes properly set `BooleanField` to `False` in all cases. ([#2776][gh2776])
* Allow `WSGIRequest.FILES` property without raising incorrect deprecated error. ([#3261][gh3261])
* Resolve issue with rendering nested serializers in forms. ([#3260][gh3260])
* Raise an error if user accidentally pass a serializer instance to a response, rather than data. ([#3241][gh3241])

### 3.2.1

**Date**: [7th August 2015][3.2.1-milestone].

* Fix for relational select widgets rendering without any choices. ([#3237][gh3237])
* Fix for `1`, `0` rendering as `true`, `false` in the admin interface. [#3227][gh3227])
* Fix for ListFields with single value in HTML form input. ([#3238][gh3238])
* Allow `request.FILES` for compat with Django's `HTTPRequest` class. ([#3239][gh3239])

### 3.2.0

**Date**: [6th August 2015][3.2.0-milestone].

* Add `AdminRenderer`. ([#2926][gh2926])
* Add `FilePathField`. ([#1854][gh1854])
* Add `allow_empty` to `ListField`. ([#2250][gh2250])
* Support django-guardian 1.3. ([#3165][gh3165])
* Support grouped choices. ([#3225][gh3225])
* Support error forms in browsable API. ([#3024][gh3024])
* Allow permission classes to customize the error message. ([#2539][gh2539])
* Support `source=<method>` on hyperlinked fields. ([#2690][gh2690])
* `ListField(allow_null=True)` now allows null as the list value, not null items in the list. ([#2766][gh2766])
* `ManyToMany()` maps to `allow_empty=False`, `ManyToMany(blank=True)` maps to `allow_empty=True`. ([#2804][gh2804])
* Support custom serialization styles for primary key fields. ([#2789][gh2789])
* `OPTIONS` requests support nested representations. ([#2915][gh2915])
* Set `view.action == "metadata"` for viewsets with `OPTIONS` requests. ([#3115][gh3115])
* Support `allow_blank` on `UUIDField`. ([#3130][gh#3130])
* Do not display view docstrings with 401 or 403 response codes. ([#3216][gh3216])
* Resolve Django 1.8 deprecation warnings. ([#2886][gh2886])
* Fix for `DecimalField` validation. ([#3139][gh3139])
* Fix behavior of `allow_blank=False` when used with `trim_whitespace=True`. ([#2712][gh2712])
* Fix issue with some field combinations incorrectly mapping to an invalid `allow_blank` argument. ([#3011][gh3011])
* Fix for output representations with prefetches and modified querysets. ([#2704][gh2704], [#2727][gh2727])
* Fix assertion error when CursorPagination is provided with certains invalid query parameters. (#2920)[gh2920].
* Fix `UnicodeDecodeError` when invalid characters included in header with `TokenAuthentication`. ([#2928][gh2928])
* Fix transaction rollbacks with `@non_atomic_requests` decorator. ([#3016][gh3016])
* Fix duplicate results issue with Oracle databases using `SearchFilter`. ([#2935][gh2935])
* Fix checkbox alignment and rendering in browsable API forms. ([#2783][gh2783])
* Fix for unsaved file objects which should use `"url": null` in the representation. ([#2759][gh2759])
* Fix field value rendering in browsable API. ([#2416][gh2416])
* Fix `HStoreField` to include `allow_blank=True` in `DictField` mapping. ([#2659][gh2659])
* Numerous other cleanups, improvements to error messaging, private API & minor fixes.

---

## 3.1.x series

### 3.1.3

**Date**: [4th June 2015][3.1.3-milestone].

* Add `DurationField`. ([#2481][gh2481], [#2989][gh2989])
* Add `format` argument to `UUIDField`. ([#2788][gh2788], [#3000][gh3000])
* `MultipleChoiceField` empties incorrectly on a partial update using multipart/form-data ([#2993][gh2993], [#2894][gh2894])
* Fix a bug in options related to read-only `RelatedField`. ([#2981][gh2981], [#2811][gh2811])
* Fix nested serializers with `unique_together` relations. ([#2975][gh2975])
* Allow unexpected values for `ChoiceField`/`MultipleChoiceField` representations. ([#2839][gh2839], [#2940][gh2940])
* Rollback the transaction on error if `ATOMIC_REQUESTS` is set. ([#2887][gh2887], [#2034][gh2034])
* Set the action on a view when override_method regardless of its None-ness. ([#2933][gh2933])
* `DecimalField` accepts `2E+2` as 200 and validates decimal place correctly. ([#2948][gh2948], [#2947][gh2947])
* Support basic authentication with custom `UserModel` that change `username`. ([#2952][gh2952])
* `IPAddressField` improvements. ([#2747][gh2747], [#2618][gh2618], [#3008][gh3008])
* Improve `DecimalField` for easier subclassing. ([#2695][gh2695])


### 3.1.2

**Date**: [13rd May 2015][3.1.2-milestone].

* `DateField.to_representation` can handle str and empty values. ([#2656][gh2656], [#2687][gh2687], [#2869][gh2869])
* Use default reason phrases from HTTP standard. ([#2764][gh2764], [#2763][gh2763])
* Raise error when `ModelSerializer` used with abstract model. ([#2757][gh2757], [#2630][gh2630])
* Handle reversal of non-API view_name in `HyperLinkedRelatedField` ([#2724][gh2724], [#2711][gh2711])
* Dont require pk strictly for related fields. ([#2745][gh2745], [#2754][gh2754])
* Metadata detects null boolean field type. ([#2762][gh2762])
* Proper handling of depth in nested serializers. ([#2798][gh2798])
* Display viewset without paginator. ([#2807][gh2807])
* Don't check for deprecated `.model` attribute in permissions ([#2818][gh2818])
* Restrict integer field to integers and strings. ([#2835][gh2835], [#2836][gh2836])
* Improve `IntegerField` to use compiled decimal regex. ([#2853][gh2853])
* Prevent empty `queryset` to raise AssertionError. ([#2862][gh2862])
* `DjangoModelPermissions` rely on `get_queryset`. ([#2863][gh2863])
* Check `AcceptHeaderVersioning` with content negotiation in place. ([#2868][gh2868])
* Allow `DjangoObjectPermissions` to use views that define `get_queryset`. ([#2905][gh2905])


### 3.1.1

**Date**: [23rd March 2015][3.1.1-milestone].

* **Security fix**: Escape tab switching cookie name in browsable API.
* Display input forms in browsable API if `serializer_class` is used, even when `get_serializer` method does not exist on the view. ([#2743][gh2743])
* Use a password input for the AuthTokenSerializer. ([#2741][gh2741])
* Fix missing anchor closing tag after next button. ([#2691][gh2691])
* Fix `lookup_url_kwarg` handling in viewsets. ([#2685][gh2685], [#2591][gh2591])
* Fix problem with importing `rest_framework.views` in `apps.py` ([#2678][gh2678])
* LimitOffsetPagination raises `TypeError` if PAGE_SIZE not set ([#2667][gh2667], [#2700][gh2700])
* German translation for `min_value` field error message references `max_value`. ([#2645][gh2645])
* Remove `MergeDict`. ([#2640][gh2640])
* Support serializing unsaved models with related fields. ([#2637][gh2637], [#2641][gh2641])
* Allow blank/null on radio.html choices. ([#2631][gh2631])


### 3.1.0

**Date**: [5th March 2015][3.1.0-milestone].

For full details see the [3.1 release announcement](3.1-announcement.md).

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

For older release notes, [please see the version 2.x documentation][old-release-notes].

[cite]: http://www.catb.org/~esr/writings/cathedral-bazaar/cathedral-bazaar/ar01s04.html
[deprecation-policy]: #deprecation-policy
[django-deprecation-policy]: https://docs.djangoproject.com/en/dev/internals/release-process/#internal-release-deprecation-policy
[defusedxml-announce]: http://blog.python.org/2013/02/announcing-defusedxml-fixes-for-xml.html
[743]: https://github.com/tomchristie/django-rest-framework/pull/743
[staticfiles14]: https://docs.djangoproject.com/en/1.4/howto/static-files/#with-a-template-tag
[staticfiles13]: https://docs.djangoproject.com/en/1.3/howto/static-files/#with-a-template-tag
[2.1.0-notes]: https://groups.google.com/d/topic/django-rest-framework/Vv2M0CMY9bg/discussion
[ticket-582]: https://github.com/tomchristie/django-rest-framework/issues/582
[rfc-6266]: http://tools.ietf.org/html/rfc6266#section-4.3
[old-release-notes]: https://github.com/tomchristie/django-rest-framework/blob/version-2.4.x/docs/topics/release-notes.md

[3.0.1-milestone]: https://github.com/tomchristie/django-rest-framework/issues?q=milestone%3A%223.0.1+Release%22
[3.0.2-milestone]: https://github.com/tomchristie/django-rest-framework/issues?q=milestone%3A%223.0.2+Release%22
[3.0.3-milestone]: https://github.com/tomchristie/django-rest-framework/issues?q=milestone%3A%223.0.3+Release%22
[3.0.4-milestone]: https://github.com/tomchristie/django-rest-framework/issues?q=milestone%3A%223.0.4+Release%22
[3.0.5-milestone]: https://github.com/tomchristie/django-rest-framework/issues?q=milestone%3A%223.0.5+Release%22
[3.1.0-milestone]: https://github.com/tomchristie/django-rest-framework/issues?q=milestone%3A%223.1.0+Release%22
[3.1.1-milestone]: https://github.com/tomchristie/django-rest-framework/issues?q=milestone%3A%223.1.1+Release%22
[3.1.2-milestone]: https://github.com/tomchristie/django-rest-framework/issues?q=milestone%3A%223.1.2+Release%22
[3.1.3-milestone]: https://github.com/tomchristie/django-rest-framework/issues?q=milestone%3A%223.1.3+Release%22
[3.2.0-milestone]: https://github.com/tomchristie/django-rest-framework/issues?q=milestone%3A%223.2.0+Release%22
[3.2.1-milestone]: https://github.com/tomchristie/django-rest-framework/issues?q=milestone%3A%223.2.1+Release%22
[3.2.2-milestone]: https://github.com/tomchristie/django-rest-framework/issues?q=milestone%3A%223.2.2+Release%22
[3.2.3-milestone]: https://github.com/tomchristie/django-rest-framework/issues?q=milestone%3A%223.2.3+Release%22
[3.2.4-milestone]: https://github.com/tomchristie/django-rest-framework/issues?q=milestone%3A%223.2.4+Release%22
[3.2.5-milestone]: https://github.com/tomchristie/django-rest-framework/issues?q=milestone%3A%223.2.5+Release%22
[3.3.0-milestone]: https://github.com/tomchristie/django-rest-framework/issues?q=milestone%3A%223.3.0+Release%22
[3.3.1-milestone]: https://github.com/tomchristie/django-rest-framework/issues?q=milestone%3A%223.3.1+Release%22
[3.3.2-milestone]: https://github.com/tomchristie/django-rest-framework/issues?q=milestone%3A%223.3.2+Release%22

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
<!-- 3.1.1 -->
[gh2691]: https://github.com/tomchristie/django-rest-framework/issues/2691
[gh2685]: https://github.com/tomchristie/django-rest-framework/issues/2685
[gh2591]: https://github.com/tomchristie/django-rest-framework/issues/2591
[gh2678]: https://github.com/tomchristie/django-rest-framework/issues/2678
[gh2667]: https://github.com/tomchristie/django-rest-framework/issues/2667
[gh2700]: https://github.com/tomchristie/django-rest-framework/issues/2700
[gh2645]: https://github.com/tomchristie/django-rest-framework/issues/2645
[gh2640]: https://github.com/tomchristie/django-rest-framework/issues/2640
[gh2637]: https://github.com/tomchristie/django-rest-framework/issues/2637
[gh2641]: https://github.com/tomchristie/django-rest-framework/issues/2641
[gh2631]: https://github.com/tomchristie/django-rest-framework/issues/2631
[gh2741]: https://github.com/tomchristie/django-rest-framework/issues/2641
[gh2743]: https://github.com/tomchristie/django-rest-framework/issues/2643
<!-- 3.1.2 -->
[gh2656]: https://github.com/tomchristie/django-rest-framework/issues/2656
[gh2687]: https://github.com/tomchristie/django-rest-framework/issues/2687
[gh2869]: https://github.com/tomchristie/django-rest-framework/issues/2869
[gh2764]: https://github.com/tomchristie/django-rest-framework/issues/2764
[gh2763]: https://github.com/tomchristie/django-rest-framework/issues/2763
[gh2757]: https://github.com/tomchristie/django-rest-framework/issues/2757
[gh2630]: https://github.com/tomchristie/django-rest-framework/issues/2630
[gh2724]: https://github.com/tomchristie/django-rest-framework/issues/2724
[gh2711]: https://github.com/tomchristie/django-rest-framework/issues/2711
[gh2745]: https://github.com/tomchristie/django-rest-framework/issues/2745
[gh2754]: https://github.com/tomchristie/django-rest-framework/issues/2754
[gh2762]: https://github.com/tomchristie/django-rest-framework/issues/2762
[gh2798]: https://github.com/tomchristie/django-rest-framework/issues/2798
[gh2807]: https://github.com/tomchristie/django-rest-framework/issues/2807
[gh2818]: https://github.com/tomchristie/django-rest-framework/issues/2818
[gh2835]: https://github.com/tomchristie/django-rest-framework/issues/2835
[gh2836]: https://github.com/tomchristie/django-rest-framework/issues/2836
[gh2853]: https://github.com/tomchristie/django-rest-framework/issues/2853
[gh2862]: https://github.com/tomchristie/django-rest-framework/issues/2862
[gh2863]: https://github.com/tomchristie/django-rest-framework/issues/2863
[gh2868]: https://github.com/tomchristie/django-rest-framework/issues/2868
[gh2905]: https://github.com/tomchristie/django-rest-framework/issues/2905
<!-- 3.1.3 -->
[gh2481]: https://github.com/tomchristie/django-rest-framework/issues/2481
[gh2989]: https://github.com/tomchristie/django-rest-framework/issues/2989
[gh2788]: https://github.com/tomchristie/django-rest-framework/issues/2788
[gh3000]: https://github.com/tomchristie/django-rest-framework/issues/3000
[gh2993]: https://github.com/tomchristie/django-rest-framework/issues/2993
[gh2894]: https://github.com/tomchristie/django-rest-framework/issues/2894
[gh2981]: https://github.com/tomchristie/django-rest-framework/issues/2981
[gh2811]: https://github.com/tomchristie/django-rest-framework/issues/2811
[gh2975]: https://github.com/tomchristie/django-rest-framework/issues/2975
[gh2839]: https://github.com/tomchristie/django-rest-framework/issues/2839
[gh2940]: https://github.com/tomchristie/django-rest-framework/issues/2940
[gh2887]: https://github.com/tomchristie/django-rest-framework/issues/2887
[gh2034]: https://github.com/tomchristie/django-rest-framework/issues/2034
[gh2933]: https://github.com/tomchristie/django-rest-framework/issues/2933
[gh2948]: https://github.com/tomchristie/django-rest-framework/issues/2948
[gh2947]: https://github.com/tomchristie/django-rest-framework/issues/2947
[gh2952]: https://github.com/tomchristie/django-rest-framework/issues/2952
[gh2747]: https://github.com/tomchristie/django-rest-framework/issues/2747
[gh2618]: https://github.com/tomchristie/django-rest-framework/issues/2618
[gh3008]: https://github.com/tomchristie/django-rest-framework/issues/3008
[gh2695]: https://github.com/tomchristie/django-rest-framework/issues/2695

<!-- 3.2.0 -->
[gh1854]: https://github.com/tomchristie/django-rest-framework/issues/1854
[gh2250]: https://github.com/tomchristie/django-rest-framework/issues/2250
[gh2416]: https://github.com/tomchristie/django-rest-framework/issues/2416
[gh2539]: https://github.com/tomchristie/django-rest-framework/issues/2539
[gh2659]: https://github.com/tomchristie/django-rest-framework/issues/2659
[gh2690]: https://github.com/tomchristie/django-rest-framework/issues/2690
[gh2704]: https://github.com/tomchristie/django-rest-framework/issues/2704
[gh2712]: https://github.com/tomchristie/django-rest-framework/issues/2712
[gh2727]: https://github.com/tomchristie/django-rest-framework/issues/2727
[gh2759]: https://github.com/tomchristie/django-rest-framework/issues/2759
[gh2766]: https://github.com/tomchristie/django-rest-framework/issues/2766
[gh2783]: https://github.com/tomchristie/django-rest-framework/issues/2783
[gh2789]: https://github.com/tomchristie/django-rest-framework/issues/2789
[gh2804]: https://github.com/tomchristie/django-rest-framework/issues/2804
[gh2886]: https://github.com/tomchristie/django-rest-framework/issues/2886
[gh2915]: https://github.com/tomchristie/django-rest-framework/issues/2915
[gh2920]: https://github.com/tomchristie/django-rest-framework/issues/2920
[gh2926]: https://github.com/tomchristie/django-rest-framework/issues/2926
[gh2928]: https://github.com/tomchristie/django-rest-framework/issues/2928
[gh2935]: https://github.com/tomchristie/django-rest-framework/issues/2935
[gh3011]: https://github.com/tomchristie/django-rest-framework/issues/3011
[gh3016]: https://github.com/tomchristie/django-rest-framework/issues/3016
[gh3024]: https://github.com/tomchristie/django-rest-framework/issues/3024
[gh3115]: https://github.com/tomchristie/django-rest-framework/issues/3115
[gh3139]: https://github.com/tomchristie/django-rest-framework/issues/3139
[gh3165]: https://github.com/tomchristie/django-rest-framework/issues/3165
[gh3216]: https://github.com/tomchristie/django-rest-framework/issues/3216
[gh3225]: https://github.com/tomchristie/django-rest-framework/issues/3225

<!-- 3.2.1 -->
[gh3237]: https://github.com/tomchristie/django-rest-framework/issues/3237
[gh3227]: https://github.com/tomchristie/django-rest-framework/issues/3227
[gh3238]: https://github.com/tomchristie/django-rest-framework/issues/3238
[gh3239]: https://github.com/tomchristie/django-rest-framework/issues/3239

<!-- 3.2.2 -->
[gh3254]: https://github.com/tomchristie/django-rest-framework/issues/3254
[gh3258]: https://github.com/tomchristie/django-rest-framework/issues/3258
[gh2776]: https://github.com/tomchristie/django-rest-framework/issues/2776
[gh3261]: https://github.com/tomchristie/django-rest-framework/issues/3261
[gh3260]: https://github.com/tomchristie/django-rest-framework/issues/3260
[gh3241]: https://github.com/tomchristie/django-rest-framework/issues/3241

<!-- 3.2.3 -->
[gh3249]: https://github.com/tomchristie/django-rest-framework/issues/3249
[gh3250]: https://github.com/tomchristie/django-rest-framework/issues/3250
[gh3275]: https://github.com/tomchristie/django-rest-framework/issues/3275
[gh3288]: https://github.com/tomchristie/django-rest-framework/issues/3288
[gh3290]: https://github.com/tomchristie/django-rest-framework/issues/3290
[gh3303]: https://github.com/tomchristie/django-rest-framework/issues/3303
[gh3313]: https://github.com/tomchristie/django-rest-framework/issues/3313
[gh3316]: https://github.com/tomchristie/django-rest-framework/issues/3316
[gh3318]: https://github.com/tomchristie/django-rest-framework/issues/3318
[gh3321]: https://github.com/tomchristie/django-rest-framework/issues/3321

<!-- 3.2.4 -->
[gh2761]: https://github.com/tomchristie/django-rest-framework/issues/2761
[gh3314]: https://github.com/tomchristie/django-rest-framework/issues/3314
[gh3323]: https://github.com/tomchristie/django-rest-framework/issues/3323
[gh3324]: https://github.com/tomchristie/django-rest-framework/issues/3324
[gh3359]: https://github.com/tomchristie/django-rest-framework/issues/3359
[gh3361]: https://github.com/tomchristie/django-rest-framework/issues/3361
[gh3364]: https://github.com/tomchristie/django-rest-framework/issues/3364
[gh3415]: https://github.com/tomchristie/django-rest-framework/issues/3415

<!-- 3.2.5 -->
[gh3550]:https://github.com/tomchristie/django-rest-framework/issues/3550

<!-- 3.3.0 -->
[gh3315]: https://github.com/tomchristie/django-rest-framework/issues/3315
[gh3410]: https://github.com/tomchristie/django-rest-framework/issues/3410
[gh3435]: https://github.com/tomchristie/django-rest-framework/issues/3435
[gh3450]: https://github.com/tomchristie/django-rest-framework/issues/3450
[gh3454]: https://github.com/tomchristie/django-rest-framework/issues/3454
[gh3475]: https://github.com/tomchristie/django-rest-framework/issues/3475
[gh3495]: https://github.com/tomchristie/django-rest-framework/issues/3495
[gh3509]: https://github.com/tomchristie/django-rest-framework/issues/3509
[gh3421]: https://github.com/tomchristie/django-rest-framework/issues/3421
[gh3525]: https://github.com/tomchristie/django-rest-framework/issues/3525
[gh3526]: https://github.com/tomchristie/django-rest-framework/issues/3526
[gh3429]: https://github.com/tomchristie/django-rest-framework/issues/3429
[gh3536]: https://github.com/tomchristie/django-rest-framework/issues/3536

<!-- 3.3.1 -->
[gh3556]: https://github.com/tomchristie/django-rest-framework/issues/3556
[gh3560]: https://github.com/tomchristie/django-rest-framework/issues/3560
[gh3564]: https://github.com/tomchristie/django-rest-framework/issues/3564
[gh3568]: https://github.com/tomchristie/django-rest-framework/issues/3568
[gh3592]: https://github.com/tomchristie/django-rest-framework/issues/3592
[gh3593]: https://github.com/tomchristie/django-rest-framework/issues/3593

<!-- 3.3.2 -->
[gh3228]: https://github.com/tomchristie/django-rest-framework/issues/3228
[gh3252]: https://github.com/tomchristie/django-rest-framework/issues/3252
[gh3513]: https://github.com/tomchristie/django-rest-framework/issues/3513
[gh3534]: https://github.com/tomchristie/django-rest-framework/issues/3534
[gh3578]: https://github.com/tomchristie/django-rest-framework/issues/3578
[gh3596]: https://github.com/tomchristie/django-rest-framework/issues/3596
[gh3597]: https://github.com/tomchristie/django-rest-framework/issues/3597
[gh3600]: https://github.com/tomchristie/django-rest-framework/issues/3600
[gh3626]: https://github.com/tomchristie/django-rest-framework/issues/3626
[gh3628]: https://github.com/tomchristie/django-rest-framework/issues/3628
[gh3631]: https://github.com/tomchristie/django-rest-framework/issues/3631
[gh3634]: https://github.com/tomchristie/django-rest-framework/issues/3634
[gh3635]: https://github.com/tomchristie/django-rest-framework/issues/3635
[gh3654]: https://github.com/tomchristie/django-rest-framework/issues/3654
[gh3655]: https://github.com/tomchristie/django-rest-framework/issues/3655
[gh3656]: https://github.com/tomchristie/django-rest-framework/issues/3656
[gh3662]: https://github.com/tomchristie/django-rest-framework/issues/3662
[gh3668]: https://github.com/tomchristie/django-rest-framework/issues/3668
[gh3672]: https://github.com/tomchristie/django-rest-framework/issues/3672
[gh3677]: https://github.com/tomchristie/django-rest-framework/issues/3677
[gh3679]: https://github.com/tomchristie/django-rest-framework/issues/3679
[gh3684]: https://github.com/tomchristie/django-rest-framework/issues/3684
[gh3687]: https://github.com/tomchristie/django-rest-framework/issues/3687
[gh3701]: https://github.com/tomchristie/django-rest-framework/issues/3701
[gh3705]: https://github.com/tomchristie/django-rest-framework/issues/3705
[gh3714]: https://github.com/tomchristie/django-rest-framework/issues/3714
[gh3718]: https://github.com/tomchristie/django-rest-framework/issues/3718
[gh3723]: https://github.com/tomchristie/django-rest-framework/issues/3723
