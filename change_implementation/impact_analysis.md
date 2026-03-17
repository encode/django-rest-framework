# DRF Issue #6855 Impact Analysis

## Scope Of The Bug

The bug affects HTML rendering through `BrowsableAPIRenderer`. It does not affect normal JSON responses or the primary view execution path.

The issue appears when all of the following are true:

1. A browsable API page is rendered.
2. The response data came from `serializer.data`, so the renderer can access `data.serializer`.
3. The serializer has `many=False`, so `serializer.instance` is used.
4. The serializer instance is not a safe object for the view's `has_object_permission()` logic.
5. The renderer probes another method, especially `OPTIONS`, during page construction.

## Observable User Impact

- The browsable API page crashes instead of rendering successfully.
- The failure happens after the view has already produced a valid response payload.
- API clients using non-HTML renderers are unaffected, so the bug can be invisible in automated API tests unless browsable rendering is exercised.

## Why Extra Actions Are A Common Trigger

Extra actions are more likely to serialize data that is not the same object type returned by `get_object()`. Examples include:

- projection objects
- service-layer result objects
- denormalized DTO-like objects
- serializer-backed views that do not call `get_object()`

That makes `serializer.instance` an unreliable proxy for object-permission checks during browsable API rendering.

## Method-Level Impact

### `OPTIONS`

This is the most important path for issue #6855.

- `OPTIONS` is typically present in `view.allowed_methods`.
- `get_context()` asks for `options_form` on normal page render.
- `get_rendered_html_form()` currently runs permission checks before its `OPTIONS` early return.
- No real serializer-bound form is produced for `OPTIONS`, so the object-level permission check is not necessary for rendering the placeholder button.

### `DELETE`

This method shares the same code shape, but the impact is different.

- `DELETE` may or may not be allowed on the route.
- `delete_form` is used to decide whether to show destructive UI.
- Unlike `OPTIONS`, object-level permission checks may still be meaningful here because the button reflects an action against a resource.

This means a broad "skip object checks for both `DELETE` and `OPTIONS`" change would be riskier than a focused `OPTIONS` fix.

### `PUT` / `PATCH`

These are not the direct cause of the reported crash for a GET-only extra action because they usually fail the `allowed_methods` check earlier. They remain important regression surface because they rely on `instance` to prepopulate edit forms.

## Compatibility Risks

### Low-risk changes

- Preventing object-permission checks for the synthetic `OPTIONS` path.
- Keeping existing permission behavior for edit and delete affordances.

### Medium-risk changes

- Replacing `serializer.instance` with `view.get_object()` inside the renderer.

This could:

- trigger additional database queries
- fail on views that do not implement `get_object()`
- introduce side effects in renderer code
- blur the boundary between response rendering and view object retrieval

### Higher-risk changes

- Skipping object-permission checks for `DELETE`
- Removing `delete_form` behavior entirely

Either could change which users see destructive UI and would need stronger review.

## Testing Impact

Regression coverage should include:

1. A browsable API request to an extra action that returns `serializer.data` for a non-model object.
2. A permission class whose `has_object_permission()` would fail if handed that serializer instance.
3. Confirmation that the HTML response renders successfully instead of crashing.
4. Confirmation that existing delete/edit form behavior is not unintentionally broadened.

Useful secondary coverage:

- a direct renderer test for the `OPTIONS` path
- confirmation that `many=True` behavior remains unchanged

## Documentation Impact

No public API documentation change is likely required if the fix is internal and behavior-preserving. A release note entry may still be appropriate because the change resolves a user-visible browsable API crash.

## Recommended Impact Conclusion

The smallest safe fix is to narrow the change to the synthetic `OPTIONS` form-generation path. That addresses the reported crash while minimizing risk to object-permission-sensitive UI such as delete and edit actions.
