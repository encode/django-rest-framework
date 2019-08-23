from rest_framework.schemas.generators import EndpointEnumerator

def test_get_path_from_regex():
    """
    Test that path from regex is correctly formatted.
    """
    path_regex = r'^entries/(?P<pk>[^/.]+)/relationships/(?P<related_field>\w+)'
    expected_path = '/entries/{pk}/relationships/{related_field}'
    enumerator = EndpointEnumerator(patterns={})
    path = enumerator.get_path_from_regex(path_regex)
    assert path == expected_path
