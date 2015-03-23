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

## 3.1.x series

### 3.1.1

**Date**: [23rd March 2015][3.1.1-milestone].

* **Security fix**: Escape tab switching cookie name in browsable API.
* Display input forms in browsable API if `serializer_class` is used, even when `get_serializer` method does not exist on the view. ([#2743](gh2743))
* Use a password input for the AuthTokenSerializer. ([#2741](gh2741))
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
