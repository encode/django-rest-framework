from __future__ import unicode_literals
from rest_framework import exceptions, generics, pagination, serializers, status, filters
from rest_framework.request import Request
from rest_framework.pagination import PageLink, PAGE_BREAK
from rest_framework.test import APIRequestFactory
import pytest

factory = APIRequestFactory()


class TestPaginationIntegration:
    """
    Integration tests.
    """

    def setup(self):
        class PassThroughSerializer(serializers.BaseSerializer):
            def to_representation(self, item):
                return item

        class EvenItemsOnly(filters.BaseFilterBackend):
            def filter_queryset(self, request, queryset, view):
                return [item for item in queryset if item % 2 == 0]

        class BasicPagination(pagination.PageNumberPagination):
            paginate_by = 5
            paginate_by_param = 'page_size'
            max_paginate_by = 20

        self.view = generics.ListAPIView.as_view(
            serializer_class=PassThroughSerializer,
            queryset=range(1, 101),
            filter_backends=[EvenItemsOnly],
            pagination_class=BasicPagination
        )

    def test_filtered_items_are_paginated(self):
        request = factory.get('/', {'page': 2})
        response = self.view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            'results': [12, 14, 16, 18, 20],
            'previous': 'http://testserver/',
            'next': 'http://testserver/?page=3',
            'count': 50
        }

    def test_setting_page_size(self):
        """
        When 'paginate_by_param' is set, the client may choose a page size.
        """
        request = factory.get('/', {'page_size': 10})
        response = self.view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            'results': [2, 4, 6, 8, 10, 12, 14, 16, 18, 20],
            'previous': None,
            'next': 'http://testserver/?page=2&page_size=10',
            'count': 50
        }

    def test_setting_page_size_over_maximum(self):
        """
        When page_size parameter exceeds maxiumum allowable,
        then it should be capped to the maxiumum.
        """
        request = factory.get('/', {'page_size': 1000})
        response = self.view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            'results': [
                2, 4, 6, 8, 10, 12, 14, 16, 18, 20,
                22, 24, 26, 28, 30, 32, 34, 36, 38, 40
            ],
            'previous': None,
            'next': 'http://testserver/?page=2&page_size=1000',
            'count': 50
        }

    def test_additional_query_params_are_preserved(self):
        request = factory.get('/', {'page': 2, 'filter': 'even'})
        response = self.view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            'results': [12, 14, 16, 18, 20],
            'previous': 'http://testserver/?filter=even',
            'next': 'http://testserver/?filter=even&page=3',
            'count': 50
        }

    def test_404_not_found_for_invalid_page(self):
        request = factory.get('/', {'page': 'invalid'})
        response = self.view(request)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data == {
            'detail': 'Invalid page "invalid": That page number is not an integer.'
        }


class TestPaginationDisabledIntegration:
    """
    Integration tests for disabled pagination.
    """

    def setup(self):
        class PassThroughSerializer(serializers.BaseSerializer):
            def to_representation(self, item):
                return item

        self.view = generics.ListAPIView.as_view(
            serializer_class=PassThroughSerializer,
            queryset=range(1, 101),
            pagination_class=None
        )

    def test_unpaginated_list(self):
        request = factory.get('/', {'page': 2})
        response = self.view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == list(range(1, 101))


class TestDeprecatedStylePagination:
    """
    Integration tests for deprecated style of setting pagination
    attributes on the view.
    """

    def setup(self):
        class PassThroughSerializer(serializers.BaseSerializer):
            def to_representation(self, item):
                return item

        class ExampleView(generics.ListAPIView):
            serializer_class = PassThroughSerializer
            queryset = range(1, 101)
            pagination_class = pagination.PageNumberPagination
            paginate_by = 20
            page_query_param = 'page_number'

        self.view = ExampleView.as_view()

    def test_paginate_by_attribute_on_view(self):
        request = factory.get('/?page_number=2')
        response = self.view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            'results': [
                21, 22, 23, 24, 25, 26, 27, 28, 29, 30,
                31, 32, 33, 34, 35, 36, 37, 38, 39, 40
            ],
            'previous': 'http://testserver/',
            'next': 'http://testserver/?page_number=3',
            'count': 100
        }


class TestPageNumberPagination:
    """
    Unit tests for `pagination.PageNumberPagination`.
    """

    def setup(self):
        class ExamplePagination(pagination.PageNumberPagination):
            paginate_by = 5
        self.pagination = ExamplePagination()
        self.queryset = range(1, 101)

    def paginate_queryset(self, request):
        return list(self.pagination.paginate_queryset(self.queryset, request))

    def get_paginated_content(self, queryset):
        response = self.pagination.get_paginated_response(queryset)
        return response.data

    def get_html_context(self):
        return self.pagination.get_html_context()

    def test_no_page_number(self):
        request = Request(factory.get('/'))
        queryset = self.paginate_queryset(request)
        content = self.get_paginated_content(queryset)
        context = self.get_html_context()
        assert queryset == [1, 2, 3, 4, 5]
        assert content == {
            'results': [1, 2, 3, 4, 5],
            'previous': None,
            'next': 'http://testserver/?page=2',
            'count': 100
        }
        assert context == {
            'previous_url': None,
            'next_url': 'http://testserver/?page=2',
            'page_links': [
                PageLink('http://testserver/', 1, True, False),
                PageLink('http://testserver/?page=2', 2, False, False),
                PageLink('http://testserver/?page=3', 3, False, False),
                PAGE_BREAK,
                PageLink('http://testserver/?page=20', 20, False, False),
            ]
        }
        assert self.pagination.display_page_controls
        assert isinstance(self.pagination.to_html(), type(''))

    def test_second_page(self):
        request = Request(factory.get('/', {'page': 2}))
        queryset = self.paginate_queryset(request)
        content = self.get_paginated_content(queryset)
        context = self.get_html_context()
        assert queryset == [6, 7, 8, 9, 10]
        assert content == {
            'results': [6, 7, 8, 9, 10],
            'previous': 'http://testserver/',
            'next': 'http://testserver/?page=3',
            'count': 100
        }
        assert context == {
            'previous_url': 'http://testserver/',
            'next_url': 'http://testserver/?page=3',
            'page_links': [
                PageLink('http://testserver/', 1, False, False),
                PageLink('http://testserver/?page=2', 2, True, False),
                PageLink('http://testserver/?page=3', 3, False, False),
                PAGE_BREAK,
                PageLink('http://testserver/?page=20', 20, False, False),
            ]
        }

    def test_last_page(self):
        request = Request(factory.get('/', {'page': 'last'}))
        queryset = self.paginate_queryset(request)
        content = self.get_paginated_content(queryset)
        context = self.get_html_context()
        assert queryset == [96, 97, 98, 99, 100]
        assert content == {
            'results': [96, 97, 98, 99, 100],
            'previous': 'http://testserver/?page=19',
            'next': None,
            'count': 100
        }
        assert context == {
            'previous_url': 'http://testserver/?page=19',
            'next_url': None,
            'page_links': [
                PageLink('http://testserver/', 1, False, False),
                PAGE_BREAK,
                PageLink('http://testserver/?page=18', 18, False, False),
                PageLink('http://testserver/?page=19', 19, False, False),
                PageLink('http://testserver/?page=20', 20, True, False),
            ]
        }

    def test_invalid_page(self):
        request = Request(factory.get('/', {'page': 'invalid'}))
        with pytest.raises(exceptions.NotFound):
            self.paginate_queryset(request)


class TestLimitOffset:
    """
    Unit tests for `pagination.LimitOffsetPagination`.
    """

    def setup(self):
        class ExamplePagination(pagination.LimitOffsetPagination):
            default_limit = 10
        self.pagination = ExamplePagination()
        self.queryset = range(1, 101)

    def paginate_queryset(self, request):
        return list(self.pagination.paginate_queryset(self.queryset, request))

    def get_paginated_content(self, queryset):
        response = self.pagination.get_paginated_response(queryset)
        return response.data

    def get_html_context(self):
        return self.pagination.get_html_context()

    def test_no_offset(self):
        request = Request(factory.get('/', {'limit': 5}))
        queryset = self.paginate_queryset(request)
        content = self.get_paginated_content(queryset)
        context = self.get_html_context()
        assert queryset == [1, 2, 3, 4, 5]
        assert content == {
            'results': [1, 2, 3, 4, 5],
            'previous': None,
            'next': 'http://testserver/?limit=5&offset=5',
            'count': 100
        }
        assert context == {
            'previous_url': None,
            'next_url': 'http://testserver/?limit=5&offset=5',
            'page_links': [
                PageLink('http://testserver/?limit=5', 1, True, False),
                PageLink('http://testserver/?limit=5&offset=5', 2, False, False),
                PageLink('http://testserver/?limit=5&offset=10', 3, False, False),
                PAGE_BREAK,
                PageLink('http://testserver/?limit=5&offset=95', 20, False, False),
            ]
        }
        assert self.pagination.display_page_controls
        assert isinstance(self.pagination.to_html(), type(''))

    def test_single_offset(self):
        """
        When the offset is not a multiple of the limit we get some edge cases:
        * The first page should still be offset zero.
        * We may end up displaying an extra page in the pagination control.
        """
        request = Request(factory.get('/', {'limit': 5, 'offset': 1}))
        queryset = self.paginate_queryset(request)
        content = self.get_paginated_content(queryset)
        context = self.get_html_context()
        assert queryset == [2, 3, 4, 5, 6]
        assert content == {
            'results': [2, 3, 4, 5, 6],
            'previous': 'http://testserver/?limit=5',
            'next': 'http://testserver/?limit=5&offset=6',
            'count': 100
        }
        assert context == {
            'previous_url': 'http://testserver/?limit=5',
            'next_url': 'http://testserver/?limit=5&offset=6',
            'page_links': [
                PageLink('http://testserver/?limit=5', 1, False, False),
                PageLink('http://testserver/?limit=5&offset=1', 2, True, False),
                PageLink('http://testserver/?limit=5&offset=6', 3, False, False),
                PAGE_BREAK,
                PageLink('http://testserver/?limit=5&offset=96', 21, False, False),
            ]
        }

    def test_first_offset(self):
        request = Request(factory.get('/', {'limit': 5, 'offset': 5}))
        queryset = self.paginate_queryset(request)
        content = self.get_paginated_content(queryset)
        context = self.get_html_context()
        assert queryset == [6, 7, 8, 9, 10]
        assert content == {
            'results': [6, 7, 8, 9, 10],
            'previous': 'http://testserver/?limit=5',
            'next': 'http://testserver/?limit=5&offset=10',
            'count': 100
        }
        assert context == {
            'previous_url': 'http://testserver/?limit=5',
            'next_url': 'http://testserver/?limit=5&offset=10',
            'page_links': [
                PageLink('http://testserver/?limit=5', 1, False, False),
                PageLink('http://testserver/?limit=5&offset=5', 2, True, False),
                PageLink('http://testserver/?limit=5&offset=10', 3, False, False),
                PAGE_BREAK,
                PageLink('http://testserver/?limit=5&offset=95', 20, False, False),
            ]
        }

    def test_middle_offset(self):
        request = Request(factory.get('/', {'limit': 5, 'offset': 10}))
        queryset = self.paginate_queryset(request)
        content = self.get_paginated_content(queryset)
        context = self.get_html_context()
        assert queryset == [11, 12, 13, 14, 15]
        assert content == {
            'results': [11, 12, 13, 14, 15],
            'previous': 'http://testserver/?limit=5&offset=5',
            'next': 'http://testserver/?limit=5&offset=15',
            'count': 100
        }
        assert context == {
            'previous_url': 'http://testserver/?limit=5&offset=5',
            'next_url': 'http://testserver/?limit=5&offset=15',
            'page_links': [
                PageLink('http://testserver/?limit=5', 1, False, False),
                PageLink('http://testserver/?limit=5&offset=5', 2, False, False),
                PageLink('http://testserver/?limit=5&offset=10', 3, True, False),
                PageLink('http://testserver/?limit=5&offset=15', 4, False, False),
                PAGE_BREAK,
                PageLink('http://testserver/?limit=5&offset=95', 20, False, False),
            ]
        }

    def test_ending_offset(self):
        request = Request(factory.get('/', {'limit': 5, 'offset': 95}))
        queryset = self.paginate_queryset(request)
        content = self.get_paginated_content(queryset)
        context = self.get_html_context()
        assert queryset == [96, 97, 98, 99, 100]
        assert content == {
            'results': [96, 97, 98, 99, 100],
            'previous': 'http://testserver/?limit=5&offset=90',
            'next': None,
            'count': 100
        }
        assert context == {
            'previous_url': 'http://testserver/?limit=5&offset=90',
            'next_url': None,
            'page_links': [
                PageLink('http://testserver/?limit=5', 1, False, False),
                PAGE_BREAK,
                PageLink('http://testserver/?limit=5&offset=85', 18, False, False),
                PageLink('http://testserver/?limit=5&offset=90', 19, False, False),
                PageLink('http://testserver/?limit=5&offset=95', 20, True, False),
            ]
        }

    def test_invalid_offset(self):
        """
        An invalid offset query param should be treated as 0.
        """
        request = Request(factory.get('/', {'limit': 5, 'offset': 'invalid'}))
        queryset = self.paginate_queryset(request)
        assert queryset == [1, 2, 3, 4, 5]

    def test_invalid_limit(self):
        """
        An invalid limit query param should be ignored in favor of the default.
        """
        request = Request(factory.get('/', {'limit': 'invalid', 'offset': 0}))
        queryset = self.paginate_queryset(request)
        assert queryset == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]


class TestCursorPagination:
    """
    Unit tests for `pagination.CursorPagination`.
    """

    def setup(self):
        class MockObject(object):
            def __init__(self, idx):
                self.created = idx

        class MockQuerySet(object):
            def __init__(self, items):
                self.items = items

            def filter(self, created__gt):
                return [
                    item for item in self.items
                    if item.created > int(created__gt)
                ]

            def __getitem__(self, sliced):
                return self.items[sliced]

        self.pagination = pagination.CursorPagination()
        self.queryset = MockQuerySet(
            [MockObject(idx) for idx in range(1, 16)]
        )

    def paginate_queryset(self, request):
        return list(self.pagination.paginate_queryset(self.queryset, request))

    # def get_paginated_content(self, queryset):
    #     response = self.pagination.get_paginated_response(queryset)
    #     return response.data

    # def get_html_context(self):
    #     return self.pagination.get_html_context()

    def test_following_cursor(self):
        request = Request(factory.get('/'))
        queryset = self.paginate_queryset(request)
        assert [item.created for item in queryset] == [1, 2, 3, 4, 5]

        next_url = self.pagination.get_next_link()
        assert next_url

        request = Request(factory.get(next_url))
        queryset = self.paginate_queryset(request)
        assert [item.created for item in queryset] == [6, 7, 8, 9, 10]

        next_url = self.pagination.get_next_link()
        assert next_url

        request = Request(factory.get(next_url))
        queryset = self.paginate_queryset(request)
        assert [item.created for item in queryset] == [11, 12, 13, 14, 15]

        next_url = self.pagination.get_next_link()
        assert next_url is None


class TestCrazyCursorPagination:
    """
    Unit tests for `pagination.CursorPagination`.
    """

    def setup(self):
        class MockObject(object):
            def __init__(self, idx):
                self.created = idx

        class MockQuerySet(object):
            def __init__(self, items):
                self.items = items

            def filter(self, created__gt):
                return [
                    item for item in self.items
                    if item.created > int(created__gt)
                ]

            def __getitem__(self, sliced):
                return self.items[sliced]

        self.pagination = pagination.CursorPagination()
        self.queryset = MockQuerySet([
            MockObject(idx) for idx in [
                1, 1, 1, 1, 1,
                1, 1, 1, 1, 1,
                1, 1, 2, 3, 4,
                5, 6, 7, 8, 9
            ]
        ])

    def paginate_queryset(self, request):
        return list(self.pagination.paginate_queryset(self.queryset, request))

    def test_following_cursor_identical_items(self):
        request = Request(factory.get('/'))
        queryset = self.paginate_queryset(request)
        assert [item.created for item in queryset] == [1, 1, 1, 1, 1]

        next_url = self.pagination.get_next_link()
        assert next_url

        request = Request(factory.get(next_url))
        queryset = self.paginate_queryset(request)
        assert [item.created for item in queryset] == [1, 1, 1, 1, 1]

        next_url = self.pagination.get_next_link()
        assert next_url

        request = Request(factory.get(next_url))
        queryset = self.paginate_queryset(request)
        assert [item.created for item in queryset] == [1, 1, 2, 3, 4]

        next_url = self.pagination.get_next_link()
        assert next_url

        request = Request(factory.get(next_url))
        queryset = self.paginate_queryset(request)
        assert [item.created for item in queryset] == [5, 6, 7, 8, 9]

        next_url = self.pagination.get_next_link()
        assert next_url is None
        # assert content == {
        #     'results': [1, 2, 3, 4, 5],
        #     'previous': None,
        #     'next': 'http://testserver/?limit=5&offset=5',
        #     'count': 100
        # }
        # assert context == {
        #     'previous_url': None,
        #     'next_url': 'http://testserver/?limit=5&offset=5',
        #     'page_links': [
        #         PageLink('http://testserver/?limit=5', 1, True, False),
        #         PageLink('http://testserver/?limit=5&offset=5', 2, False, False),
        #         PageLink('http://testserver/?limit=5&offset=10', 3, False, False),
        #         PAGE_BREAK,
        #         PageLink('http://testserver/?limit=5&offset=95', 20, False, False),
        #     ]
        # }
        # assert self.pagination.display_page_controls
        # assert isinstance(self.pagination.to_html(), type(''))


def test_get_displayed_page_numbers():
    """
    Test our contextual page display function.

    This determines which pages to display in a pagination control,
    given the current page and the last page.
    """
    displayed_page_numbers = pagination._get_displayed_page_numbers

    # At five pages or less, all pages are displayed, always.
    assert displayed_page_numbers(1, 5) == [1, 2, 3, 4, 5]
    assert displayed_page_numbers(2, 5) == [1, 2, 3, 4, 5]
    assert displayed_page_numbers(3, 5) == [1, 2, 3, 4, 5]
    assert displayed_page_numbers(4, 5) == [1, 2, 3, 4, 5]
    assert displayed_page_numbers(5, 5) == [1, 2, 3, 4, 5]

    # Between six and either pages we may have a single page break.
    assert displayed_page_numbers(1, 6) == [1, 2, 3, None, 6]
    assert displayed_page_numbers(2, 6) == [1, 2, 3, None, 6]
    assert displayed_page_numbers(3, 6) == [1, 2, 3, 4, 5, 6]
    assert displayed_page_numbers(4, 6) == [1, 2, 3, 4, 5, 6]
    assert displayed_page_numbers(5, 6) == [1, None, 4, 5, 6]
    assert displayed_page_numbers(6, 6) == [1, None, 4, 5, 6]

    assert displayed_page_numbers(1, 7) == [1, 2, 3, None, 7]
    assert displayed_page_numbers(2, 7) == [1, 2, 3, None, 7]
    assert displayed_page_numbers(3, 7) == [1, 2, 3, 4, None, 7]
    assert displayed_page_numbers(4, 7) == [1, 2, 3, 4, 5, 6, 7]
    assert displayed_page_numbers(5, 7) == [1, None, 4, 5, 6, 7]
    assert displayed_page_numbers(6, 7) == [1, None, 5, 6, 7]
    assert displayed_page_numbers(7, 7) == [1, None, 5, 6, 7]

    assert displayed_page_numbers(1, 8) == [1, 2, 3, None, 8]
    assert displayed_page_numbers(2, 8) == [1, 2, 3, None, 8]
    assert displayed_page_numbers(3, 8) == [1, 2, 3, 4, None, 8]
    assert displayed_page_numbers(4, 8) == [1, 2, 3, 4, 5, None, 8]
    assert displayed_page_numbers(5, 8) == [1, None, 4, 5, 6, 7, 8]
    assert displayed_page_numbers(6, 8) == [1, None, 5, 6, 7, 8]
    assert displayed_page_numbers(7, 8) == [1, None, 6, 7, 8]
    assert displayed_page_numbers(8, 8) == [1, None, 6, 7, 8]

    # At nine or more pages we may have two page breaks, one on each side.
    assert displayed_page_numbers(1, 9) == [1, 2, 3, None, 9]
    assert displayed_page_numbers(2, 9) == [1, 2, 3, None, 9]
    assert displayed_page_numbers(3, 9) == [1, 2, 3, 4, None, 9]
    assert displayed_page_numbers(4, 9) == [1, 2, 3, 4, 5, None, 9]
    assert displayed_page_numbers(5, 9) == [1, None, 4, 5, 6, None, 9]
    assert displayed_page_numbers(6, 9) == [1, None, 5, 6, 7, 8, 9]
    assert displayed_page_numbers(7, 9) == [1, None, 6, 7, 8, 9]
    assert displayed_page_numbers(8, 9) == [1, None, 7, 8, 9]
    assert displayed_page_numbers(9, 9) == [1, None, 7, 8, 9]
