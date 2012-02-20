Release Notes
=============

0.3.3
-----

* Added DjangoModelPermissions class to support `django.contrib.auth` style permissions.
* Use `staticfiles` for css files.
  - Easier to override.  Won't conflict with customised admin styles (eg grappelli)
* Templates are now nicely namespaced.
  - Allows easier overriding.
* Drop implied 'pk' filter if last arg in urlconf is unnamed.
  - Too magical.  Explict is better than implicit.
* Saner template variable autoescaping.
* Tider setup.py
* Updated for URLObject 2.0
* Bugfixes:
  - Bug with PerUserThrottling when user contains unicode chars.

0.3.2
-----

* Bugfixes:
  * Fix 403 for POST and PUT from the UI with UserLoggedInAuthentication (#115)
  * serialize_model method in serializer.py may cause wrong value (#73)
  * Fix Error when clicking OPTIONS button (#146)
  * And many other fixes
* Remove short status codes
  - Zen of Python: "There should be one-- and preferably only one --obvious way to do it."
* get_name, get_description become methods on the view - makes them overridable.
* Improved model mixin API - Hooks for build_query, get_instance_data, get_model, get_queryset, get_ordering

0.3.1
-----

* [not documented]

0.3.0
-----

* JSONP Support
* Bugfixes, including support for latest markdown release

0.2.4
-----

* Fix broken IsAdminUser permission.
* OPTIONS support.
* XMLParser.
* Drop mentions of Blog, BitBucket.

0.2.3
-----

* Fix some throttling bugs.
* ``X-Throttle`` header on throttling.
* Support for nesting resources on related models.

0.2.2
-----

* Throttling support complete.

0.2.1
-----

* Couple of simple bugfixes over 0.2.0

0.2.0
-----

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

0.1.1
-----

* Final build before pulling in all the refactoring changes for 0.2, in case anyone needs to hang on to 0.1.

0.1.0
-----

* Initial release.
