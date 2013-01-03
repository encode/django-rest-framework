# Release Notes

> Release Early, Release Often
>
> &mdash; Eric S. Raymond, [The Cathedral and the Bazaar][cite].

## Versioning

Minor version numbers (0.0.x) are used for changes that are API compatible.  You should be able to upgrade between minor point releases without any other code changes.

Medium version numbers (0.x.0) may include minor API changes.  You should read the release notes carefully before upgrading between medium point releases.

Major version numbers (x.0.0) are reserved for project milestones.  No major point releases are currently planned.

---

## 2.1.x series

### Master

* Added `PATCH` support.
* Added `RetrieveUpdateAPIView`.
* Relation changes are now persisted in `save` instead of in `.restore_object`.
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

**Note**: From 2.1.14 onwards, relational fields move out of the `fields.py` module and into the new `relations.py` module, in order to seperate them from regular data type fields, such as `CharField` and `IntegerField`.

This change will not affect user code, so long as it's following the recommended import style of `from rest_framework import serializers` and refering to fields using the style `serializers.PrimaryKeyRelatedField`.


### 2.1.13

**Date**: 28th Dec 2012

* Support configurable `STATICFILES_STORAGE` storage.
* Bugfix: Related fields now respect the required flag, and may be required=False.

### 2.1.12

**Date**: 21st Dec 2012

* Bugfix: Fix bug that could occur using ChoiceField.
* Bugfix: Fix exception in browseable API on DELETE.
* Bugfix: Fix issue where pk was was being set to a string if set by URL kwarg.

### 2.1.11

**Date**: 17th Dec 2012

* Bugfix: Fix issue with M2M fields in browseable API.

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
* Bugfix: Support choice field in Browseable API.
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

---

## 0.4.x series

### 0.4.0

* Supports Django 1.5.
* Fixes issues with 'HEAD' method.
* Allow views to specify template used by TemplateRenderer
* More consistent error responses
* Some serializer fixes
* Fix internet explorer ajax behavior
* Minor xml and yaml fixes
* Improve setup (e.g. use staticfiles, not the defunct ADMIN_MEDIA_PREFIX)
* Sensible absolute URL generation, not using hacky set_script_prefix

---

## 0.3.x series

### 0.3.3

* Added DjangoModelPermissions class to support `django.contrib.auth` style permissions.
* Use `staticfiles` for css files.
  - Easier to override.  Won't conflict with customized admin styles (e.g. grappelli)
* Templates are now nicely namespaced.
  - Allows easier overriding.
* Drop implied 'pk' filter if last arg in urlconf is unnamed.
  - Too magical.  Explicit is better than implicit.
* Saner template variable auto-escaping.
* Tidier setup.py
* Updated for URLObject 2.0
* Bugfixes:
  - Bug with PerUserThrottling when user contains unicode chars.

### 0.3.2

* Bugfixes:
  * Fix 403 for POST and PUT from the UI with UserLoggedInAuthentication (#115)
  * serialize_model method in serializer.py may cause wrong value (#73)
  * Fix Error when clicking OPTIONS button (#146)
  * And many other fixes
* Remove short status codes
  - Zen of Python: "There should be one-- and preferably only one --obvious way to do it."
* get_name, get_description become methods on the view - makes them overridable.
* Improved model mixin API - Hooks for build_query, get_instance_data, get_model, get_queryset, get_ordering

### 0.3.1

* [not documented]

### 0.3.0

* JSONP Support
* Bugfixes, including support for latest markdown release

---

## 0.2.x series

### 0.2.4

* Fix broken IsAdminUser permission.
* OPTIONS support.
* XMLParser.
* Drop mentions of Blog, BitBucket.

### 0.2.3

* Fix some throttling bugs.
* ``X-Throttle`` header on throttling.
* Support for nesting resources on related models.

### 0.2.2

* Throttling support complete.

### 0.2.1

* Couple of simple bugfixes over 0.2.0

### 0.2.0

* Big refactoring changes since 0.1.0, ask on the discussion group if anything isn't clear.
  The public API has been massively cleaned up.  Expect it to be fairly stable from here on in.

* ``Resource`` becomes decoupled into ``View`` and ``Resource``, your views should now inherit from ``View``, not ``Resource``.

* The handler functions on views ``.get() .put() .post()`` etc, no longer have the ``content`` and ``auth`` args.
  Use ``self.CONTENT`` inside a view to access the deserialized, validated content.
  Use ``self.user`` inside a view to access the authenticated user.

* ``allowed_methods`` and ``anon_allowed_methods`` are now defunct.  if a method is defined, it's available.
  The ``permissions`` attribute on a ``View`` is now used to provide generic permissions checking.
  Use permission classes such as ``FullAnonAccess``, ``IsAuthenticated`` or ``IsUserOrIsAnonReadOnly`` to set the permissions.

* The ``authenticators`` class becomes ``authentication``.  Class names change to ``Authentication``.

* The ``emitters`` class becomes ``renderers``.  Class names change to ``Renderers``.

* ``ResponseException`` becomes ``ErrorResponse``.

* The mixin classes have been nicely refactored, the basic mixins are now ``RequestMixin``, ``ResponseMixin``, ``AuthMixin``, and ``ResourceMixin``
  You can reuse these mixin classes individually without using the ``View`` class.

---

## 0.1.x series

### 0.1.1

* Final build before pulling in all the refactoring changes for 0.2, in case anyone needs to hang on to 0.1.

### 0.1.0

* Initial release.

[cite]: http://www.catb.org/~esr/writings/cathedral-bazaar/cathedral-bazaar/ar01s04.html
[staticfiles14]: https://docs.djangoproject.com/en/1.4/howto/static-files/#with-a-template-tag
[staticfiles13]: https://docs.djangoproject.com/en/1.3/howto/static-files/#with-a-template-tag
[2.1.0-notes]: https://groups.google.com/d/topic/django-rest-framework/Vv2M0CMY9bg/discussion
[announcement]: rest-framework-2-announcement.md
