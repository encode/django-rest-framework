from rest_framework.schemas.generators import EndpointEnumerator

def test_get_path_from_regex():
    """
    Test that path from regex is correctly formatted.
    """
    path_regex = r'^entries/(?P<pk>[^/.]+)/relationships/(?P<related_field>\w+)'
    path_regex_trailing = path_regex + '/'
    expected_path = '/entries/{pk}/relationships/{related_field}'
    expected_path_trailing = expected_path + '/'
    enumerator = EndpointEnumerator(patterns={})
    path_trailing = enumerator.get_path_from_regex(path_regex_trailing)
    assert path_trailing == expected_path_trailing

    path = enumerator.get_path_from_regex(path_regex)
    assert path == expected_path
