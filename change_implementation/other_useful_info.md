## Quick Overview of Important Classes

Inside `rest_framework/`, common areas are:

`serializers.py`: converts Python/Django objects to API data and validates input.
`views.py`, `generics.py`, `viewsets.py`: request handling abstractions.
`routers.py`: URL routing for viewsets.
`permissions.py`, `authentication.py`, `throttling.py`: access control and API policies.
`renderers.py`, `parsers.py`: output/input formats like JSON and the browsable API.
`response.py`, `request.py`: DRF’s request/response wrappers.

## Issue in Plain English

Issue #6855 is a Browsable API bug. The actual API endpoint works, but the HTML page crashes while DRF is trying to decide which buttons/forms to show.

The key flow is:

- A view action returns `Response(serializer.data)`.
- In browsable mode, DRF looks at `data.serializer`.
- It pulls `serializer.instance`.
- It uses that instance for permission checks while deciding whether to show forms/buttons.
- For some extra actions, that serializer.instance is not the real model object the permission logic expects.
- Result: DRF calls object-permission logic on the wrong kind of object and crashes.

This is the critical code path:

```python
# renderers.py
def show_form_for_method(self, view, method, request, obj):
    """
    Returns True if a form should be shown for this method.
    """
    if method not in view.allowed_methods:
        return  # Not a valid method

    try:
        view.check_permissions(request)
        if obj is not None:
            view.check_object_permissions(request, obj)
```

And this is where the renderer derives the object from the serializer and then asks for forms for several methods:

```python
# renderers.py
# See issue #2089 for refactoring this.
serializer = getattr(data, 'serializer', None)
if serializer and not getattr(serializer, 'many', False):
    instance = getattr(serializer, 'instance', None)
    if isinstance(instance, Page):
        instance = None
else:
    instance = None

with override_method(view, request, method) as request:
    if not self.show_form_for_method(view, method, request, instance):
        return

    if method in ('DELETE', 'OPTIONS'):
        return True  # Don't actually need to return a form
```

And the browsable page always probes multiple methods, even on a normal GET render:

```python
# renderers.py
'put_form': self.get_rendered_html_form(data, view, 'PUT', request),
'post_form': self.get_rendered_html_form(data, view, 'POST', request),
'delete_form': self.get_rendered_html_form(data, view, 'DELETE', request),
'options_form': self.get_rendered_html_form(data, view, 'OPTIONS', request),
```
