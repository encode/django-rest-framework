# DRF Issue #6855 Concept Location

## Problem Summary

The browsable API can crash while rendering an extra action page when the response data comes from a serializer whose `instance` is not a normal model object for the current view's permission class.

The failing path is in the browsable API renderer, not in view dispatch:

1. The extra action returns `Response(serializer.data)`.
2. `serializer.data` is a `ReturnDict` or `ReturnList` that keeps a backlink to the serializer.
3. `BrowsableAPIRenderer` inspects that serializer during HTML rendering.
4. While building placeholder UI for other HTTP methods, it calls `view.check_object_permissions(request, instance)`.
5. `instance` may be a non-model object from the serializer, which can be incompatible with the permission class and crash with `AttributeError`.

## Primary Source Locations

### `rest_framework/renderers.py`

This is the main issue location.

- `BrowsableAPIRenderer.get_context()`
  - Always asks for `put_form`, `post_form`, `delete_form`, and `options_form`.
  - This means a normal `GET` render also evaluates synthetic UI for other methods.

- `BrowsableAPIRenderer.get_rendered_html_form()`
  - Pulls `serializer = getattr(data, 'serializer', None)`.
  - Extracts `instance = getattr(serializer, 'instance', None)` when `many=False`.
  - Calls `show_form_for_method()` before the current `DELETE` / `OPTIONS` bailout.
  - This ordering is what exposes the bug.

- `BrowsableAPIRenderer.show_form_for_method()`
  - Calls `view.check_permissions(request)`.
  - If `obj is not None`, also calls `view.check_object_permissions(request, obj)`.
  - Only catches `APIException`, so an unexpected `AttributeError` from a permission class bubbles up and crashes rendering.

## Supporting Locations

### `rest_framework/utils/serializer_helpers.py`

- `ReturnDict`
- `ReturnList`

These wrappers preserve `data.serializer`, which is why renderers can see the original serializer and its `.instance`.

### `rest_framework/views.py`

- `APIView.check_object_permissions()`

This loops through permission classes and directly passes the provided object to `has_object_permission()`. It assumes the caller supplied the correct domain object.

### `rest_framework/request.py`

- `override_method`

`get_rendered_html_form()` uses this context manager while probing alternate HTTP methods such as `OPTIONS` and `DELETE`.

## UI/Template Locations

### `rest_framework/templates/rest_framework/base.html`

- `options_form`
- `delete_form`

These booleans control whether the browsable API shows the `OPTIONS` button and `DELETE` button/modal.

### `rest_framework/templates/rest_framework/admin.html`

- `delete_form`

The admin renderer also consumes the truthiness of `delete_form`.

## Existing Test Locations To Extend

### `tests/test_renderers.py`

Contains `BrowsableAPIRendererTests`, which is the closest existing unit/integration coverage for renderer behavior and extra actions.

### `tests/browsable_api/test_form_rendering.py`

Already has regression coverage around browsable API form generation and serializer shapes, including `many=True`.

### `tests/browsable_api/views.py`

Contains an example object-permission class that accesses nested attributes on the object and is useful as a pattern for reproducing this class of failure.

## Key Conceptual Insight

The renderer is mixing two different concepts:

- the object that was serialized for display
- the object that should be used for permission checks when deciding whether to show action UI

For issue #6855, the immediate crash is triggered by the synthetic `OPTIONS` UI path, where no object-level edit form is actually rendered, so reusing `serializer.instance` is not appropriate.
