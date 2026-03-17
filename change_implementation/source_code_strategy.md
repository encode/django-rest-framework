# DRF Issue #6855 Source Code Strategy

## Goal

Fix the browsable API crash for extra actions that return serializer-backed data whose `serializer.instance` is not a valid object for the view's object-permission logic.

## Recommended Strategy

Implement a focused change in `rest_framework/renderers.py` so that the synthetic `OPTIONS` button path does not call `check_object_permissions()` on `serializer.instance`.

## Why This Strategy

It directly addresses the reported crash with the smallest behavioral change.

It also preserves current behavior for methods where object-level permission checks are still meaningful:

- `PUT`
- `PATCH`
- `DELETE`

## Proposed Code Change

### Primary change

Refactor `BrowsableAPIRenderer.get_rendered_html_form()` so that `OPTIONS` is handled before `show_form_for_method(view, method, request, instance)` is called.

Recommended behavior:

1. Enter `override_method(view, request, method)` as today.
2. If `method == 'OPTIONS'`:
   - return early when the method is not allowed
   - run `view.check_permissions(request)`
   - do not run `view.check_object_permissions(request, instance)`
   - return `True` so the template can render the `OPTIONS` button
3. For all other methods, keep the existing `show_form_for_method()` flow.
4. Keep the existing `DELETE` truthy return after permission gating.

## Why Not Use `view.get_object()`

Avoid changing the renderer to retrieve a new object from the view.

Reasons:

- not every relevant view implements `get_object()`
- extra actions may intentionally not be tied to the routed object
- renderer-time object lookup can introduce extra queries and side effects
- it is a larger semantic change than needed for this bug

## Why Not Skip Checks For Both `DELETE` And `OPTIONS`

That would be simpler mechanically, but it risks changing existing UI authorization behavior for delete actions.

`OPTIONS` is different because the renderer does not build an object-bound form for it. It only needs enough permission context to decide whether the method is generally accessible.

## Suggested Test Plan

### Regression test

Add a renderer-focused regression test in `tests/test_renderers.py` near `BrowsableAPIRendererTests`.

Suggested test shape:

1. Define a `ViewSet` with browsable API enabled.
2. Add a detail extra action that returns `Response(serializer.data)`.
3. Use a serializer whose `instance` is a custom object without the attributes expected by object permissions.
4. Attach a permission class whose `has_object_permission()` would raise `AttributeError` if called with that custom object.
5. Request the extra action with `HTTP_ACCEPT='text/html'`.
6. Assert that the response renders successfully with status `200`.

### Guardrail test

Add a small test confirming that delete UI still respects the existing permission gate, or at minimum ensure no existing delete-related renderer test regresses when the new test is added.

### Optional unit test

If maintainers prefer tighter isolation, add a direct unit test around `get_rendered_html_form(..., method='OPTIONS', ...)` to assert the method returns truthy without consulting object permissions.

## Implementation Notes

- Keep the fix local to `BrowsableAPIRenderer`; avoid changing core permission APIs.
- Do not broaden exception handling to swallow arbitrary `AttributeError`. That would hide real bugs instead of correcting the invalid permission-check input.
- Preserve the current `many=True` behavior, where `instance` is already treated as `None`.

## Validation Steps

1. Run the new regression test.
2. Run existing browsable API renderer tests.
3. Verify no change in non-HTML renderer behavior.
4. Manually confirm that an authenticated browsable API extra action page now renders instead of crashing.

## Fallback Option

If reviewers want a more centralized fix, a secondary approach is to teach `show_form_for_method()` to skip object-permission checks only for `OPTIONS`. That is still acceptable, but the `get_rendered_html_form()`-level change keeps the special case closest to the synthetic-form behavior that causes the bug.
