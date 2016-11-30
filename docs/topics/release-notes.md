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

## 3.5.x series

### 3.5.3

**Date**: [7th November 2016][3.5.3-milestone]

* Don't raise incorrect FilterSet deprecation warnings. ([#4660][gh4660], [#4643][gh4643], [#4644][gh4644])
* Schema generation should not raise 404 when a view permission class does. ([#4645][gh4645], [#4646][gh4646])
* Add `autofocus` support for input controls. ([#4650][gh4650])

### 3.5.2

**Date**: [1st November 2016][3.5.2-milestone]

* Restore exception tracebacks in Python 2.7. ([#4631][gh4631], [#4638][gh4638])
* Properly display dicts in the admin console. ([#4532][gh4532], [#4636][gh4636])
* Fix is_simple_callable with variable args, kwargs. ([#4622][gh4622], [#4602][gh4602])
* Support 'on'/'off' literals with BooleanField. ([#4640][gh4640], [#4624][gh4624])
* Enable cursor pagination of value querysets. ([#4569][gh4569])
* Fix support of get_full_details() for Throttled exceptions. ([#4627][gh4627])
* Fix FilterSet proxy. ([#4620][gh4620])
* Make serializer fields import explicit. ([#4628][gh4628])
* Drop redundant requests adapter. ([#4639][gh4639])

### 3.5.1

**Date**: [21st October 2016][3.5.1-milestone]

* Make `rest_framework/compat.py` imports. ([#4612][gh4612], [#4608][gh4608], [#4601][gh4601])
* Fix bug in schema base path generation. ([#4611][gh4611], [#4605][gh4605])
* Fix broken case of ListSerializer with single item. ([#4609][gh4609], [#4606][gh4606])
* Remove bare `raise` for Python 3.5 compat. ([#4600][gh4600])

### 3.5.0

**Date**: [20th October 2016][3.5.0-milestone]

---

## 3.4.x series

### 3.4.7

**Date**: [21st September 2016][3.4.7-milestone]

* Fallback behavior for request parsing when request.POST already accessed. ([#3951][gh3951], [#4500][gh4500])
* Fix regression of `RegexField`. ([#4489][gh4489], [#4490][gh4490], [#2617][gh2617])
* Missing comma in `admin.html` causing CSRF error. ([#4472][gh4472], [#4473][gh4473])
* Fix response rendering with empty context. ([#4495][gh4495])
* Fix indentation regression in API listing. ([#4493][gh4493])
* Fixed an issue where the incorrect value is set to `ResolverMatch.func_name` of api_view decorated view. ([#4465][gh4465], [#4462][gh4462])
* Fix `APIClient.get()` when path contains unicode arguments ([#4458][gh4458])

### 3.4.6

**Date**: [23rd August 2016][3.4.6-milestone]

* Fix malformed Javascript in browsable API. ([#4435][gh4435])
* Skip HiddenField from Schema fields. ([#4425][gh4425], [#4429][gh4429])
* Improve Create to show the original exception traceback. ([#3508][gh3508])
* Fix `AdminRenderer` display of PK only related fields. ([#4419][gh4419], [#4423][gh4423])

### 3.4.5

**Date**: [19th August 2016][3.4.5-milestone]

* Improve debug error handling. ([#4416][gh4416], [#4409][gh4409])
* Allow custom CSRF_HEADER_NAME setting. ([#4415][gh4415], [#4410][gh4410])
* Include .action attribute on viewsets when generating schemas. ([#4408][gh4408], [#4398][gh4398])
* Do not include request.FILES items in request.POST. ([#4407][gh4407])
* Fix rendering of checkbox multiple. ([#4403][gh4403])
* Fix docstring of Field.get_default. ([#4404][gh4404])
* Replace utf8 character with its ascii counterpart in README. ([#4412][gh4412])

### 3.4.4

**Date**: [12th August 2016][3.4.4-milestone]

* Ensure views are fully initialized when generating schemas. ([#4373][gh4373], [#4382][gh4382], [#4383][gh4383], [#4279][gh4279], [#4278][gh4278])
* Add form field descriptions to schemas. ([#4387][gh4387])
* Fix category generation for schema endpoints. ([#4391][gh4391], [#4394][gh4394], [#4390][gh4390], [#4386][gh4386], [#4376][gh4376], [#4329][gh4329])
* Don't strip empty query params when paginating. ([#4392][gh4392], [#4393][gh4393], [#4260][gh4260])
* Do not re-run query for empty results with LimitOffsetPagination. ([#4201][gh4201], [#4388][gh4388])
* Stricter type validation for CharField. ([#4380][gh4380], [#3394][gh3394])
* RelatedField.choices should preserve non-string values. ([#4111][gh4111], [#4379][gh4379], [#3365][gh3365])
* Test case for rendering checkboxes in vertical form style. ([#4378][gh4378], [#3868][gh3868], [#3868][gh3868])
* Show error traceback HTML in browsable API ([#4042][gh4042], [#4172][gh4172])
* Fix handling of ALLOWED_VERSIONS and no DEFAULT_VERSION. [#4370][gh4370]
* Allow `max_digits=None` on DecimalField. ([#4377][gh4377], [#4372][gh4372])
* Limit queryset when rendering relational choices. ([#4375][gh4375], [#4122][gh4122], [#3329][gh3329], [#3330][gh3330], [#3877][gh3877])
* Resolve form display with ChoiceField, MultipleChoiceField and non-string choices. ([#4374][gh4374], [#4119][gh4119], [#4121][gh4121], [#4137][gh4137], [#4120][gh4120])
* Fix call to TemplateHTMLRenderer.resolve_context() fallback method. ([#4371][gh4371])

### 3.4.3

**Date**: [5th August 2016][3.4.3-milestone]

* Include fallaback for users of older TemplateHTMLRenderer internal API. ([#4361][gh4361])

### 3.4.2

**Date**: [5th August 2016][3.4.2-milestone]

* Include kwargs passed to 'as_view' when generating schemas. ([#4359][gh4359], [#4330][gh4330], [#4331][gh4331])
* Access `request.user.is_authenticated` as property not method, under Django 1.10+ ([#4358][gh4358], [#4354][gh4354])
* Filter HEAD out from schemas. ([#4357][gh4357])
* extra_kwargs takes precedence over uniqueness kwargs. ([#4198][gh4198], [#4199][gh4199], [#4349][gh4349])
* Correct descriptions when tabs are used in code indentation. ([#4345][gh4345], [#4347][gh4347])*
* Change template context generation in TemplateHTMLRenderer. ([#4236][gh4236])
* Serializer defaults should not be included in partial updates. ([#4346][gh4346], [#3565][gh3565])
* Consistent behavior & descriptive error from FileUploadParser when filename not included. ([#4340][gh4340], [#3610][gh3610], [#4292][gh4292], [#4296][gh4296])
* DecimalField quantizes incoming digitals. ([#4339][gh4339], [#4318][gh4318])
* Handle non-string input for IP fields. ([#4335][gh4335], [#4336][gh4336], [#4338][gh4338])
* Fix leading slash handling when Schema generation includes a root URL. ([#4332][gh4332])
* Test cases for DictField with allow_null options. ([#4348][gh4348])
* Update tests from Django 1.10 beta to Django 1.10. ([#4344][gh4344])

### 3.4.1

**Date**: [28th July 2016][3.4.1-milestone]

* Added `root_renderers` argument to `DefaultRouter`. ([#4323][gh4323], [#4268][gh4268])
* Added `url` and `schema_url` arguments. ([#4321][gh4321], [#4308][gh4308], [#4305][gh4305])
* Unique together checks should apply to read-only fields which have a default. ([#4316][gh4316], [#4294][gh4294])
* Set view.format_kwarg in schema generator. ([#4293][gh4293], [#4315][gh4315])
* Fix schema generator for views with `pagination_class = None`. ([#4314][gh4314], [#4289][gh4289])
* Fix schema generator for views with no `get_serializer_class`. ([#4265][gh4265], [#4285][gh4285])
* Fixes for media type parameters in `Accept` and `Content-Type` headers. ([#4287][gh4287], [#4313][gh4313], [#4281][gh4281])
* Use verbose_name instead of object_name in error messages. ([#4299][gh4299])
* Minor version update to Twitter Bootstrap. ([#4307][gh4307])
* SearchFilter raises error when using with related field. ([#4302][gh4302], [#4303][gh4303], [#4298][gh4298])
* Adding support for RFC 4918 status codes. ([#4291][gh4291])
* Add LICENSE.md to the built wheel. ([#4270][gh4270])
* Serializing "complex" field returns None instead of the value since 3.4 ([#4272][gh4272], [#4273][gh4273], [#4288][gh4288])

### 3.4.0

**Date**: [14th July 2016][3.4.0-milestone]

* Don't strip microseconds in JSON output. ([#4256][gh4256])
* Two slightly different iso 8601 datetime serialization. ([#4255][gh4255])
* Resolve incorrect inclusion of media type parameters. ([#4254][gh4254])
* Response Content-Type potentially malformed. ([#4253][gh4253])
* Fix setup.py error on some platforms. ([#4246][gh4246])
* Move alternate formats in coreapi into separate packages. ([#4244][gh4244])
* Add localize keyword argument to `DecimalField`. ([#4233][gh4233])
* Fix issues with routers for custom list-route and detail-routes. ([#4229][gh4229])
* Namespace versioning with nested namespaces. ([#4219][gh4219])
* Robust uniqueness checks. ([#4217][gh4217])
* Minor refactoring of `must_call_distinct`. ([#4215][gh4215])
* Overridable offset cutoff in CursorPagination. ([#4212][gh4212])
* Pass through strings as-in with date/time fields. ([#4196][gh4196])
* Add test confirming that required=False is valid on a relational field. ([#4195][gh4195])
* In LimitOffsetPagination `limit=0` should revert to default limit. ([#4194][gh4194])
* Exclude read_only=True fields from unique_together validation & add docs. ([#4192][gh4192])
* Handle bytestrings in JSON. ([#4191][gh4191])
* JSONField(binary=True) represents using binary strings, which JSONRenderer does not support. ([#4187][gh4187])
* JSONField(binary=True) represents using binary strings, which JSONRenderer does not support. ([#4185][gh4185])
* More robust form rendering in the browsable API. ([#4181][gh4181])
* Empty cases of `.validated_data` and `.errors` as lists not dicts for ListSerializer. ([#4180][gh4180])
* Schemas & client libraries. ([#4179][gh4179])
* Removed `AUTH_USER_MODEL` compat property. ([#4176][gh4176])
* Clean up existing deprecation warnings. ([#4166][gh4166])
* Django 1.10 support. ([#4158][gh4158])
* Updated jQuery version to 1.12.4. ([#4157][gh4157])
* More robust default behavior on OrderingFilter. ([#4156][gh4156])
* description.py codes and tests removal. ([#4153][gh4153])
* Wrap guardian.VERSION in tuple. ([#4149][gh4149])
* Refine validator for fields with <source=> kwargs. ([#4146][gh4146])
* Fix None values representation in childs of ListField, DictField. ([#4118][gh4118])
* Resolve TimeField representation for midnight value. ([#4107][gh4107])
* Set proper status code in AdminRenderer for the redirection after POST/DELETE requests. ([#4106][gh4106])
* TimeField render returns None instead of 00:00:00. ([#4105][gh4105])
* Fix incorrectly named zh-hans and zh-hant locale path. ([#4103][gh4103])
* Prevent raising exception when limit is 0. ([#4098][gh4098])
* TokenAuthentication: Allow custom keyword in the header. ([#4097][gh4097])
* Handle incorrectly padded HTTP basic auth header. ([#4090][gh4090])
* LimitOffset pagination crashes Browseable API when limit=0. ([#4079][gh4079])
* Fixed DecimalField arbitrary precision support. ([#4075][gh4075])
* Added support for custom CSRF cookie names. ([#4049][gh4049])
* Fix regression introduced by #4035. ([#4041][gh4041])
* No auth view failing permission should raise 403. ([#4040][gh4040])
* Fix string_types / text_types confusion. ([#4025][gh4025])
* Do not list related field choices in OPTIONS requests. ([#4021][gh4021])
* Fix typo. ([#4008][gh4008])
* Reorder initializing the view. ([#4006][gh4006])
* Type error in DjangoObjectPermissionsFilter on Python 3.4. ([#4005][gh4005])
* Fixed use of deprecated Query.aggregates. ([#4003][gh4003])
* Fix blank lines around docstrings. ([#4002][gh4002])
* Fixed admin pagination when limit is 0. ([#3990][gh3990])
* OrderingFilter adjustements. ([#3983][gh3983])
* Non-required serializer related fields. ([#3976][gh3976])
* Using safer calling way of "@api_view" in tutorial. ([#3971][gh3971])
* ListSerializer doesn't handle unique_together constraints. ([#3970][gh3970])
* Add missing migration file. ([#3968][gh3968])
* `OrderingFilter` should call `get_serializer_class()` to determine default fields. ([#3964][gh3964])
* Remove old django checks from tests and compat. ([#3953][gh3953])
* Support callable as the value of `initial` for any `serializer.Field`. ([#3943][gh3943])
* Prevented unnecessary distinct() call in SearchFilter. ([#3938][gh3938])
* Fix None UUID ForeignKey serialization. ([#3936][gh3936])
* Drop EOL Django 1.7. ([#3933][gh3933])
* Add missing space in serializer error message. ([#3926][gh3926])
* Fixed _force_text_recursive typo. ([#3908][gh3908])
* Attempt to address Django 2.0 deprecate warnings related to `field.rel`. ([#3906][gh3906])
* Fix parsing multipart data using a nested serializer with list. ([#3820][gh3820])
* Resolving APIs URL to different namespaces. ([#3816][gh3816])
* Do not HTML-escape `help_text` in Browsable API forms. ([#3812][gh3812])
* OPTIONS fetches and shows all possible foreign keys in choices field. ([#3751][gh3751])
* Django 1.9 deprecation warnings ([#3729][gh3729])
* Test case for #3598 ([#3710][gh3710])
* Adding support for multiple values for search filter. ([#3541][gh3541])
* Use get_serializer_class in ordering filter. ([#3487][gh3487])
* Serializers with many=True should return empty list rather than empty dict. ([#3476][gh3476])
* LimitOffsetPagination limit=0 fix. ([#3444][gh3444])
* Enable Validators to defer string evaluation and handle new string format. ([#3438][gh3438])
* Unique validator is executed and breaks if field is invalid. ([#3381][gh3381])
* Do not ignore overridden View.get_view_name() in breadcrumbs. ([#3273][gh3273])
* Retry form rendering when rendering with serializer fails. ([#3164][gh3164])
* Unique constraint prevents nested serializers from updating. ([#2996][gh2996])
* Uniqueness validators should not be run for excluded (read_only) fields. ([#2848][gh2848])
* UniqueValidator raises exception for nested objects. ([#2403][gh2403])
* `lookup_type` is deprecated in favor of `lookup_expr`. ([#4259][gh4259])
---

## 3.3.x series

### 3.3.3

**Date**: [14th March 2016][3.3.3-milestone].

* Remove version string from templates. Thanks to @blag for the report and fixes. ([#3878][gh3878], [#3913][gh3913], [#3912][gh3912])
* Fixes vertical html layout for `BooleanField`. Thanks to Mikalai Radchuk for the fix. ([#3910][gh3910])
* Silenced deprecation warnings on Django 1.8. Thanks to Simon Charette for the fix. ([#3903][gh3903])
* Internationalization for authtoken. Thanks to Michael Nacharov for the fix. ([#3887][gh3887], [#3968][gh3968])
* Fix `Token` model as `abstract` when the authtoken application isn't declared. Thanks to Adam Thomas for the report. ([#3860][gh3860], [#3858][gh3858])
* Improve Markdown version compatibility. Thanks to Michael J. Schultz for the fix. ([#3604][gh3604], [#3842][gh3842])
* `QueryParameterVersioning` does not use `DEFAULT_VERSION` setting. Thanks to Brad Montgomery for the fix. ([#3833][gh3833])
* Add an explicit `on_delete` on the models. Thanks to Mads Jensen for the fix. ([#3832][gh3832])
* Fix `DateField.to_representation` to work with Python 2 unicode. Thanks to Mikalai Radchuk for the fix. ([#3819][gh3819])
* Fixed `TimeField` not handling string times. Thanks to Areski Belaid for the fix. ([#3809][gh3809])
* Avoid updates of `Meta.extra_kwargs`. Thanks to Kevin Massey for the report and fix. ([#3805][gh3805], [#3804][gh3804])
* Fix nested validation error being rendered incorrectly. Thanks to Craig de Stigter for the fix. ([#3801][gh3801])
* Document how to avoid CSRF and missing button issues with `django-crispy-forms`. Thanks to Emmanuelle Delescolle, José Padilla and Luis San Pablo for the report, analysis and fix. ([#3787][gh3787], [#3636][gh3636], [#3637][gh3637])
* Improve Rest Framework Settings file setup time. Thanks to Miles Hutson for the report and Mads Jensen for the fix. ([#3786][gh3786], [#3815][gh3815])
* Improve authtoken compatibility with Django 1.9. Thanks to S. Andrew Sheppard for the fix. ([#3785][gh3785])
* Fix `Min/MaxValueValidator` transfer from a model's `DecimalField`. Thanks to Kevin Brown for the fix. ([#3774][gh3774])
* Improve HTML title in the Browsable API. Thanks to Mike Lissner for the report and fix. ([#3769][gh3769])
* Fix `AutoFilterSet` to inherit from `default_filter_set`. Thanks to Tom Linford for the fix. ([#3753][gh3753])
* Fix transifex config to handle the new Chinese language codes. Thanks to @nypisces for the report and fix. ([#3739][gh3739])
* `DateTimeField` does not handle empty values correctly. Thanks to Mick Parker for the report and fix. ([#3731][gh3731], [#3726][gh3728])
* Raise error when setting a removed rest_framework setting. Thanks to Luis San Pablo for the fix. ([#3715][gh3715])
* Add missing csrf_token in AdminRenderer post form. Thanks to Piotr Śniegowski for the fix. ([#3703][gh3703])
* Refactored `_get_reverse_relationships()` to use correct `to_field`. Thanks to Benjamin Phillips for the fix. ([#3696][gh3696])
* Document the use of `get_queryset` for `RelatedField`. Thanks to Ryan Hiebert for the fix. ([#3605][gh3605])
* Fix empty pk detection in HyperlinkRelatedField.get_url. Thanks to @jslang for the fix ([#3962][gh3962])

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

---

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
[django-deprecation-policy]: https://docs.djangoproject.com/en/stable/internals/release-process/#internal-release-deprecation-policy
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
[3.3.3-milestone]: https://github.com/tomchristie/django-rest-framework/issues?q=milestone%3A%223.3.3+Release%22
[3.4.0-milestone]: https://github.com/tomchristie/django-rest-framework/issues?q=milestone%3A%223.4.0+Release%22
[3.4.1-milestone]: https://github.com/tomchristie/django-rest-framework/issues?q=milestone%3A%223.4.1+Release%22
[3.4.2-milestone]: https://github.com/tomchristie/django-rest-framework/issues?q=milestone%3A%223.4.2+Release%22
[3.4.3-milestone]: https://github.com/tomchristie/django-rest-framework/issues?q=milestone%3A%223.4.3+Release%22
[3.4.4-milestone]: https://github.com/tomchristie/django-rest-framework/issues?q=milestone%3A%223.4.4+Release%22
[3.4.5-milestone]: https://github.com/tomchristie/django-rest-framework/issues?q=milestone%3A%223.4.5+Release%22
[3.4.6-milestone]: https://github.com/tomchristie/django-rest-framework/issues?q=milestone%3A%223.4.6+Release%22
[3.4.7-milestone]: https://github.com/tomchristie/django-rest-framework/issues?q=milestone%3A%223.4.7+Release%22
[3.5.0-milestone]: https://github.com/tomchristie/django-rest-framework/issues?q=milestone%3A%223.5.0+Release%22
[3.5.1-milestone]: https://github.com/tomchristie/django-rest-framework/issues?q=milestone%3A%223.5.1+Release%22
[3.5.2-milestone]: https://github.com/tomchristie/django-rest-framework/issues?q=milestone%3A%223.5.2+Release%22
[3.5.3-milestone]: https://github.com/tomchristie/django-rest-framework/issues?q=milestone%3A%223.5.3+Release%22

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

<!-- 3.3.3 -->
[gh3968]: https://github.com/tomchristie/django-rest-framework/issues/3968
[gh3962]: https://github.com/tomchristie/django-rest-framework/issues/3962
[gh3913]: https://github.com/tomchristie/django-rest-framework/issues/3913
[gh3912]: https://github.com/tomchristie/django-rest-framework/issues/3912
[gh3910]: https://github.com/tomchristie/django-rest-framework/issues/3910
[gh3903]: https://github.com/tomchristie/django-rest-framework/issues/3903
[gh3887]: https://github.com/tomchristie/django-rest-framework/issues/3887
[gh3878]: https://github.com/tomchristie/django-rest-framework/issues/3878
[gh3860]: https://github.com/tomchristie/django-rest-framework/issues/3860
[gh3858]: https://github.com/tomchristie/django-rest-framework/issues/3858
[gh3842]: https://github.com/tomchristie/django-rest-framework/issues/3842
[gh3833]: https://github.com/tomchristie/django-rest-framework/issues/3833
[gh3832]: https://github.com/tomchristie/django-rest-framework/issues/3832
[gh3819]: https://github.com/tomchristie/django-rest-framework/issues/3819
[gh3815]: https://github.com/tomchristie/django-rest-framework/issues/3815
[gh3809]: https://github.com/tomchristie/django-rest-framework/issues/3809
[gh3805]: https://github.com/tomchristie/django-rest-framework/issues/3805
[gh3804]: https://github.com/tomchristie/django-rest-framework/issues/3804
[gh3801]: https://github.com/tomchristie/django-rest-framework/issues/3801
[gh3787]: https://github.com/tomchristie/django-rest-framework/issues/3787
[gh3786]: https://github.com/tomchristie/django-rest-framework/issues/3786
[gh3785]: https://github.com/tomchristie/django-rest-framework/issues/3785
[gh3774]: https://github.com/tomchristie/django-rest-framework/issues/3774
[gh3769]: https://github.com/tomchristie/django-rest-framework/issues/3769
[gh3753]: https://github.com/tomchristie/django-rest-framework/issues/3753
[gh3739]: https://github.com/tomchristie/django-rest-framework/issues/3739
[gh3731]: https://github.com/tomchristie/django-rest-framework/issues/3731
[gh3728]: https://github.com/tomchristie/django-rest-framework/issues/3726
[gh3715]: https://github.com/tomchristie/django-rest-framework/issues/3715
[gh3703]: https://github.com/tomchristie/django-rest-framework/issues/3703
[gh3696]: https://github.com/tomchristie/django-rest-framework/issues/3696
[gh3637]: https://github.com/tomchristie/django-rest-framework/issues/3637
[gh3636]: https://github.com/tomchristie/django-rest-framework/issues/3636
[gh3605]: https://github.com/tomchristie/django-rest-framework/issues/3605
[gh3604]: https://github.com/tomchristie/django-rest-framework/issues/3604

<!-- 3.4.0 -->
[gh2403]: https://github.com/tomchristie/django-rest-framework/issues/2403
[gh2848]: https://github.com/tomchristie/django-rest-framework/issues/2848
[gh2996]: https://github.com/tomchristie/django-rest-framework/issues/2996
[gh3164]: https://github.com/tomchristie/django-rest-framework/issues/3164
[gh3273]: https://github.com/tomchristie/django-rest-framework/issues/3273
[gh3381]: https://github.com/tomchristie/django-rest-framework/issues/3381
[gh3438]: https://github.com/tomchristie/django-rest-framework/issues/3438
[gh3444]: https://github.com/tomchristie/django-rest-framework/issues/3444
[gh3476]: https://github.com/tomchristie/django-rest-framework/issues/3476
[gh3487]: https://github.com/tomchristie/django-rest-framework/issues/3487
[gh3541]: https://github.com/tomchristie/django-rest-framework/issues/3541
[gh3710]: https://github.com/tomchristie/django-rest-framework/issues/3710
[gh3729]: https://github.com/tomchristie/django-rest-framework/issues/3729
[gh3751]: https://github.com/tomchristie/django-rest-framework/issues/3751
[gh3812]: https://github.com/tomchristie/django-rest-framework/issues/3812
[gh3816]: https://github.com/tomchristie/django-rest-framework/issues/3816
[gh3820]: https://github.com/tomchristie/django-rest-framework/issues/3820
[gh3906]: https://github.com/tomchristie/django-rest-framework/issues/3906
[gh3908]: https://github.com/tomchristie/django-rest-framework/issues/3908
[gh3926]: https://github.com/tomchristie/django-rest-framework/issues/3926
[gh3933]: https://github.com/tomchristie/django-rest-framework/issues/3933
[gh3936]: https://github.com/tomchristie/django-rest-framework/issues/3936
[gh3938]: https://github.com/tomchristie/django-rest-framework/issues/3938
[gh3943]: https://github.com/tomchristie/django-rest-framework/issues/3943
[gh3953]: https://github.com/tomchristie/django-rest-framework/issues/3953
[gh3964]: https://github.com/tomchristie/django-rest-framework/issues/3964
[gh3968]: https://github.com/tomchristie/django-rest-framework/issues/3968
[gh3970]: https://github.com/tomchristie/django-rest-framework/issues/3970
[gh3971]: https://github.com/tomchristie/django-rest-framework/issues/3971
[gh3976]: https://github.com/tomchristie/django-rest-framework/issues/3976
[gh3983]: https://github.com/tomchristie/django-rest-framework/issues/3983
[gh3990]: https://github.com/tomchristie/django-rest-framework/issues/3990
[gh4002]: https://github.com/tomchristie/django-rest-framework/issues/4002
[gh4003]: https://github.com/tomchristie/django-rest-framework/issues/4003
[gh4005]: https://github.com/tomchristie/django-rest-framework/issues/4005
[gh4006]: https://github.com/tomchristie/django-rest-framework/issues/4006
[gh4008]: https://github.com/tomchristie/django-rest-framework/issues/4008
[gh4021]: https://github.com/tomchristie/django-rest-framework/issues/4021
[gh4025]: https://github.com/tomchristie/django-rest-framework/issues/4025
[gh4040]: https://github.com/tomchristie/django-rest-framework/issues/4040
[gh4041]: https://github.com/tomchristie/django-rest-framework/issues/4041
[gh4049]: https://github.com/tomchristie/django-rest-framework/issues/4049
[gh4075]: https://github.com/tomchristie/django-rest-framework/issues/4075
[gh4079]: https://github.com/tomchristie/django-rest-framework/issues/4079
[gh4090]: https://github.com/tomchristie/django-rest-framework/issues/4090
[gh4097]: https://github.com/tomchristie/django-rest-framework/issues/4097
[gh4098]: https://github.com/tomchristie/django-rest-framework/issues/4098
[gh4103]: https://github.com/tomchristie/django-rest-framework/issues/4103
[gh4105]: https://github.com/tomchristie/django-rest-framework/issues/4105
[gh4106]: https://github.com/tomchristie/django-rest-framework/issues/4106
[gh4107]: https://github.com/tomchristie/django-rest-framework/issues/4107
[gh4118]: https://github.com/tomchristie/django-rest-framework/issues/4118
[gh4146]: https://github.com/tomchristie/django-rest-framework/issues/4146
[gh4149]: https://github.com/tomchristie/django-rest-framework/issues/4149
[gh4153]: https://github.com/tomchristie/django-rest-framework/issues/4153
[gh4156]: https://github.com/tomchristie/django-rest-framework/issues/4156
[gh4157]: https://github.com/tomchristie/django-rest-framework/issues/4157
[gh4158]: https://github.com/tomchristie/django-rest-framework/issues/4158
[gh4166]: https://github.com/tomchristie/django-rest-framework/issues/4166
[gh4176]: https://github.com/tomchristie/django-rest-framework/issues/4176
[gh4179]: https://github.com/tomchristie/django-rest-framework/issues/4179
[gh4180]: https://github.com/tomchristie/django-rest-framework/issues/4180
[gh4181]: https://github.com/tomchristie/django-rest-framework/issues/4181
[gh4185]: https://github.com/tomchristie/django-rest-framework/issues/4185
[gh4187]: https://github.com/tomchristie/django-rest-framework/issues/4187
[gh4191]: https://github.com/tomchristie/django-rest-framework/issues/4191
[gh4192]: https://github.com/tomchristie/django-rest-framework/issues/4192
[gh4194]: https://github.com/tomchristie/django-rest-framework/issues/4194
[gh4195]: https://github.com/tomchristie/django-rest-framework/issues/4195
[gh4196]: https://github.com/tomchristie/django-rest-framework/issues/4196
[gh4212]: https://github.com/tomchristie/django-rest-framework/issues/4212
[gh4215]: https://github.com/tomchristie/django-rest-framework/issues/4215
[gh4217]: https://github.com/tomchristie/django-rest-framework/issues/4217
[gh4219]: https://github.com/tomchristie/django-rest-framework/issues/4219
[gh4229]: https://github.com/tomchristie/django-rest-framework/issues/4229
[gh4233]: https://github.com/tomchristie/django-rest-framework/issues/4233
[gh4244]: https://github.com/tomchristie/django-rest-framework/issues/4244
[gh4246]: https://github.com/tomchristie/django-rest-framework/issues/4246
[gh4253]: https://github.com/tomchristie/django-rest-framework/issues/4253
[gh4254]: https://github.com/tomchristie/django-rest-framework/issues/4254
[gh4255]: https://github.com/tomchristie/django-rest-framework/issues/4255
[gh4256]: https://github.com/tomchristie/django-rest-framework/issues/4256
[gh4259]: https://github.com/tomchristie/django-rest-framework/issues/4259

<!-- 3.4.1 -->
[gh4323]: https://github.com/tomchristie/django-rest-framework/issues/4323
[gh4268]: https://github.com/tomchristie/django-rest-framework/issues/4268
[gh4321]: https://github.com/tomchristie/django-rest-framework/issues/4321
[gh4308]: https://github.com/tomchristie/django-rest-framework/issues/4308
[gh4305]: https://github.com/tomchristie/django-rest-framework/issues/4305
[gh4316]: https://github.com/tomchristie/django-rest-framework/issues/4316
[gh4294]: https://github.com/tomchristie/django-rest-framework/issues/4294
[gh4293]: https://github.com/tomchristie/django-rest-framework/issues/4293
[gh4315]: https://github.com/tomchristie/django-rest-framework/issues/4315
[gh4314]: https://github.com/tomchristie/django-rest-framework/issues/4314
[gh4289]: https://github.com/tomchristie/django-rest-framework/issues/4289
[gh4265]: https://github.com/tomchristie/django-rest-framework/issues/4265
[gh4285]: https://github.com/tomchristie/django-rest-framework/issues/4285
[gh4287]: https://github.com/tomchristie/django-rest-framework/issues/4287
[gh4313]: https://github.com/tomchristie/django-rest-framework/issues/4313
[gh4281]: https://github.com/tomchristie/django-rest-framework/issues/4281
[gh4299]: https://github.com/tomchristie/django-rest-framework/issues/4299
[gh4307]: https://github.com/tomchristie/django-rest-framework/issues/4307
[gh4302]: https://github.com/tomchristie/django-rest-framework/issues/4302
[gh4303]: https://github.com/tomchristie/django-rest-framework/issues/4303
[gh4298]: https://github.com/tomchristie/django-rest-framework/issues/4298
[gh4291]: https://github.com/tomchristie/django-rest-framework/issues/4291
[gh4270]: https://github.com/tomchristie/django-rest-framework/issues/4270
[gh4272]: https://github.com/tomchristie/django-rest-framework/issues/4272
[gh4273]: https://github.com/tomchristie/django-rest-framework/issues/4273
[gh4288]: https://github.com/tomchristie/django-rest-framework/issues/4288

<!-- 3.4.2 -->
[gh3565]: https://github.com/tomchristie/django-rest-framework/issues/3565
[gh3610]: https://github.com/tomchristie/django-rest-framework/issues/3610
[gh4198]: https://github.com/tomchristie/django-rest-framework/issues/4198
[gh4199]: https://github.com/tomchristie/django-rest-framework/issues/4199
[gh4236]: https://github.com/tomchristie/django-rest-framework/issues/4236
[gh4292]: https://github.com/tomchristie/django-rest-framework/issues/4292
[gh4296]: https://github.com/tomchristie/django-rest-framework/issues/4296
[gh4318]: https://github.com/tomchristie/django-rest-framework/issues/4318
[gh4330]: https://github.com/tomchristie/django-rest-framework/issues/4330
[gh4331]: https://github.com/tomchristie/django-rest-framework/issues/4331
[gh4332]: https://github.com/tomchristie/django-rest-framework/issues/4332
[gh4335]: https://github.com/tomchristie/django-rest-framework/issues/4335
[gh4336]: https://github.com/tomchristie/django-rest-framework/issues/4336
[gh4338]: https://github.com/tomchristie/django-rest-framework/issues/4338
[gh4339]: https://github.com/tomchristie/django-rest-framework/issues/4339
[gh4340]: https://github.com/tomchristie/django-rest-framework/issues/4340
[gh4344]: https://github.com/tomchristie/django-rest-framework/issues/4344
[gh4345]: https://github.com/tomchristie/django-rest-framework/issues/4345
[gh4346]: https://github.com/tomchristie/django-rest-framework/issues/4346
[gh4347]: https://github.com/tomchristie/django-rest-framework/issues/4347
[gh4348]: https://github.com/tomchristie/django-rest-framework/issues/4348
[gh4349]: https://github.com/tomchristie/django-rest-framework/issues/4349
[gh4354]: https://github.com/tomchristie/django-rest-framework/issues/4354
[gh4357]: https://github.com/tomchristie/django-rest-framework/issues/4357
[gh4358]: https://github.com/tomchristie/django-rest-framework/issues/4358
[gh4359]: https://github.com/tomchristie/django-rest-framework/issues/4359

<!-- 3.4.3 -->
[gh4361]: https://github.com/tomchristie/django-rest-framework/issues/4361

<!-- 3.4.4 -->

[gh2829]: https://github.com/tomchristie/django-rest-framework/issues/2829
[gh3329]: https://github.com/tomchristie/django-rest-framework/issues/3329
[gh3330]: https://github.com/tomchristie/django-rest-framework/issues/3330
[gh3365]: https://github.com/tomchristie/django-rest-framework/issues/3365
[gh3394]: https://github.com/tomchristie/django-rest-framework/issues/3394
[gh3868]: https://github.com/tomchristie/django-rest-framework/issues/3868
[gh3868]: https://github.com/tomchristie/django-rest-framework/issues/3868
[gh3877]: https://github.com/tomchristie/django-rest-framework/issues/3877
[gh4042]: https://github.com/tomchristie/django-rest-framework/issues/4042
[gh4111]: https://github.com/tomchristie/django-rest-framework/issues/4111
[gh4119]: https://github.com/tomchristie/django-rest-framework/issues/4119
[gh4120]: https://github.com/tomchristie/django-rest-framework/issues/4120
[gh4121]: https://github.com/tomchristie/django-rest-framework/issues/4121
[gh4122]: https://github.com/tomchristie/django-rest-framework/issues/4122
[gh4137]: https://github.com/tomchristie/django-rest-framework/issues/4137
[gh4172]: https://github.com/tomchristie/django-rest-framework/issues/4172
[gh4201]: https://github.com/tomchristie/django-rest-framework/issues/4201
[gh4260]: https://github.com/tomchristie/django-rest-framework/issues/4260
[gh4278]: https://github.com/tomchristie/django-rest-framework/issues/4278
[gh4279]: https://github.com/tomchristie/django-rest-framework/issues/4279
[gh4329]: https://github.com/tomchristie/django-rest-framework/issues/4329
[gh4370]: https://github.com/tomchristie/django-rest-framework/issues/4370
[gh4371]: https://github.com/tomchristie/django-rest-framework/issues/4371
[gh4372]: https://github.com/tomchristie/django-rest-framework/issues/4372
[gh4373]: https://github.com/tomchristie/django-rest-framework/issues/4373
[gh4374]: https://github.com/tomchristie/django-rest-framework/issues/4374
[gh4375]: https://github.com/tomchristie/django-rest-framework/issues/4375
[gh4376]: https://github.com/tomchristie/django-rest-framework/issues/4376
[gh4377]: https://github.com/tomchristie/django-rest-framework/issues/4377
[gh4378]: https://github.com/tomchristie/django-rest-framework/issues/4378
[gh4379]: https://github.com/tomchristie/django-rest-framework/issues/4379
[gh4380]: https://github.com/tomchristie/django-rest-framework/issues/4380
[gh4382]: https://github.com/tomchristie/django-rest-framework/issues/4382
[gh4383]: https://github.com/tomchristie/django-rest-framework/issues/4383
[gh4386]: https://github.com/tomchristie/django-rest-framework/issues/4386
[gh4387]: https://github.com/tomchristie/django-rest-framework/issues/4387
[gh4388]: https://github.com/tomchristie/django-rest-framework/issues/4388
[gh4390]: https://github.com/tomchristie/django-rest-framework/issues/4390
[gh4391]: https://github.com/tomchristie/django-rest-framework/issues/4391
[gh4392]: https://github.com/tomchristie/django-rest-framework/issues/4392
[gh4393]: https://github.com/tomchristie/django-rest-framework/issues/4393
[gh4394]: https://github.com/tomchristie/django-rest-framework/issues/4394

<!-- 3.4.5 -->
[gh4416]: https://github.com/tomchristie/django-rest-framework/issues/4416
[gh4409]: https://github.com/tomchristie/django-rest-framework/issues/4409
[gh4415]: https://github.com/tomchristie/django-rest-framework/issues/4415
[gh4410]: https://github.com/tomchristie/django-rest-framework/issues/4410
[gh4408]: https://github.com/tomchristie/django-rest-framework/issues/4408
[gh4398]: https://github.com/tomchristie/django-rest-framework/issues/4398
[gh4407]: https://github.com/tomchristie/django-rest-framework/issues/4407
[gh4403]: https://github.com/tomchristie/django-rest-framework/issues/4403
[gh4404]: https://github.com/tomchristie/django-rest-framework/issues/4404
[gh4412]: https://github.com/tomchristie/django-rest-framework/issues/4412

<!-- 3.4.6 -->

[gh4435]: https://github.com/tomchristie/django-rest-framework/issues/4435
[gh4425]: https://github.com/tomchristie/django-rest-framework/issues/4425
[gh4429]: https://github.com/tomchristie/django-rest-framework/issues/4429
[gh3508]: https://github.com/tomchristie/django-rest-framework/issues/3508
[gh4419]: https://github.com/tomchristie/django-rest-framework/issues/4419
[gh4423]: https://github.com/tomchristie/django-rest-framework/issues/4423

<!-- 3.4.7 -->

[gh3951]: https://github.com/tomchristie/django-rest-framework/issues/3951
[gh4500]: https://github.com/tomchristie/django-rest-framework/issues/4500
[gh4489]: https://github.com/tomchristie/django-rest-framework/issues/4489
[gh4490]: https://github.com/tomchristie/django-rest-framework/issues/4490
[gh2617]: https://github.com/tomchristie/django-rest-framework/issues/2617
[gh4472]: https://github.com/tomchristie/django-rest-framework/issues/4472
[gh4473]: https://github.com/tomchristie/django-rest-framework/issues/4473
[gh4495]: https://github.com/tomchristie/django-rest-framework/issues/4495
[gh4493]: https://github.com/tomchristie/django-rest-framework/issues/4493
[gh4465]: https://github.com/tomchristie/django-rest-framework/issues/4465
[gh4462]: https://github.com/tomchristie/django-rest-framework/issues/4462
[gh4458]: https://github.com/tomchristie/django-rest-framework/issues/4458

<!-- 3.5.1 -->

[gh4612]: https://github.com/tomchristie/django-rest-framework/issues/4612
[gh4608]: https://github.com/tomchristie/django-rest-framework/issues/4608
[gh4601]: https://github.com/tomchristie/django-rest-framework/issues/4601
[gh4611]: https://github.com/tomchristie/django-rest-framework/issues/4611
[gh4605]: https://github.com/tomchristie/django-rest-framework/issues/4605
[gh4609]: https://github.com/tomchristie/django-rest-framework/issues/4609
[gh4606]: https://github.com/tomchristie/django-rest-framework/issues/4606
[gh4600]: https://github.com/tomchristie/django-rest-framework/issues/4600

<!-- 3.5.2 -->

[gh4631]: https://github.com/tomchristie/django-rest-framework/issues/4631
[gh4638]: https://github.com/tomchristie/django-rest-framework/issues/4638
[gh4532]: https://github.com/tomchristie/django-rest-framework/issues/4532
[gh4636]: https://github.com/tomchristie/django-rest-framework/issues/4636
[gh4622]: https://github.com/tomchristie/django-rest-framework/issues/4622
[gh4602]: https://github.com/tomchristie/django-rest-framework/issues/4602
[gh4640]: https://github.com/tomchristie/django-rest-framework/issues/4640
[gh4624]: https://github.com/tomchristie/django-rest-framework/issues/4624
[gh4569]: https://github.com/tomchristie/django-rest-framework/issues/4569
[gh4627]: https://github.com/tomchristie/django-rest-framework/issues/4627
[gh4620]: https://github.com/tomchristie/django-rest-framework/issues/4620
[gh4628]: https://github.com/tomchristie/django-rest-framework/issues/4628
[gh4639]: https://github.com/tomchristie/django-rest-framework/issues/4639

<!-- 3.5.3 -->

[gh4660]: https://github.com/tomchristie/django-rest-framework/issues/4660
[gh4643]: https://github.com/tomchristie/django-rest-framework/issues/4643
[gh4644]: https://github.com/tomchristie/django-rest-framework/issues/4644
[gh4645]: https://github.com/tomchristie/django-rest-framework/issues/4645
[gh4646]: https://github.com/tomchristie/django-rest-framework/issues/4646
[gh4650]: https://github.com/tomchristie/django-rest-framework/issues/4650
