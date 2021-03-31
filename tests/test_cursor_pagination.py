import base64
import itertools
from base64 import b64encode
from urllib import parse

import pytest
from rest_framework import generics
from rest_framework.pagination import Cursor, CursorPagination
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import AllowAny
from rest_framework.serializers import ModelSerializer
from rest_framework.test import APIRequestFactory
from .models import ExamplePaginationModel


factory = APIRequestFactory()


class SerializerCls(ModelSerializer):
    class Meta:
        model = ExamplePaginationModel
        fields = "__all__"


def create_cursor(offset, reverse, position):
    # Taken from rest_framework.pagination
    cursor = Cursor(offset=offset, reverse=reverse, position=position)

    tokens = {}
    if cursor.offset != 0:
        tokens["o"] = str(cursor.offset)
    if cursor.reverse:
        tokens["r"] = "1"
    if cursor.position is not None:
        tokens["p"] = cursor.position

    querystring = parse.urlencode(tokens, doseq=True)
    return b64encode(querystring.encode("ascii")).decode("ascii")


def decode_cursor(response):
    links = {
        'next': response.data.get('next'),
        'prev': response.data.get('prev'),
    }

    cursors = {}

    for rel, link in links.items():
        if link:
            # Don't hate my laziness - copied from an IPDB prompt
            cursor_dict = dict(
                parse.parse_qsl(
                    base64.decodebytes(
                        (parse.parse_qs(parse.urlparse(link).query)["cursor"][0]).encode()
                    )
                )
            )

            offset = cursor_dict.get(b"o", 0)
            if offset:
                offset = int(offset)

            reverse = cursor_dict.get(b"r", False)
            if reverse:
                reverse = int(reverse)

            position = cursor_dict.get(b"p", None)

            cursors[rel] = Cursor(
                offset=offset,
                reverse=reverse,
                position=position,
            )

    return type(
        "prev_next_stuct",
        (object,),
        {"next": cursors.get("next"), "prev": cursors.get("previous")},
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "page_size,offset",
    [
        (6, 2), (2, 6), (5, 3), (3, 5), (5, 5)
    ],
    ids=[
        'page_size_divisor_of_offset',
        'page_size_multiple_of_offset',
        'page_size_uneven_divisor_of_offset',
        'page_size_uneven_multiple_of_offset',
        'page_size_same_as_offset',
    ]
)
def test_filtered_items_are_paginated(page_size, offset):

    PaginationCls = type('PaginationCls', (CursorPagination,), dict(
        page_size=page_size,
        offset_cutoff=offset,
        max_page_size=20,
    ))

    example_models = []

    for id_, (field_1, field_2) in enumerate(
        itertools.product(range(1, 11), range(1, 3))
    ):
        # field_1 is a unique range from 1-10 inclusive
        # field_2 is the 'timestamp' field. 1 or 2
        example_models.append(
            ExamplePaginationModel(
                # manual primary key
                id=id_ + 1,
                field=field_1,
                timestamp=field_2,
            )
        )

    ExamplePaginationModel.objects.bulk_create(example_models)

    view = generics.ListAPIView.as_view(
        serializer_class=SerializerCls,
        queryset=ExamplePaginationModel.objects.all(),
        pagination_class=PaginationCls,
        permission_classes=(AllowAny,),
        filter_backends=[OrderingFilter],
    )

    def _request(offset, reverse, position):
        return view(
            factory.get(
                "/",
                {
                    PaginationCls.cursor_query_param: create_cursor(
                        offset, reverse, position
                    ),
                    "ordering": "timestamp,id",
                },
            )
        )

    # This is the result we would expect
    expected_result = list(
        ExamplePaginationModel.objects.order_by("timestamp", "id").values(
            "timestamp",
            "id",
            "field",
        )
    )
    assert expected_result == [
        {"field": 1, "id": 1, "timestamp": 1},
        {"field": 2, "id": 3, "timestamp": 1},
        {"field": 3, "id": 5, "timestamp": 1},
        {"field": 4, "id": 7, "timestamp": 1},
        {"field": 5, "id": 9, "timestamp": 1},
        {"field": 6, "id": 11, "timestamp": 1},
        {"field": 7, "id": 13, "timestamp": 1},
        {"field": 8, "id": 15, "timestamp": 1},
        {"field": 9, "id": 17, "timestamp": 1},
        {"field": 10, "id": 19, "timestamp": 1},
        {"field": 1, "id": 2, "timestamp": 2},
        {"field": 2, "id": 4, "timestamp": 2},
        {"field": 3, "id": 6, "timestamp": 2},
        {"field": 4, "id": 8, "timestamp": 2},
        {"field": 5, "id": 10, "timestamp": 2},
        {"field": 6, "id": 12, "timestamp": 2},
        {"field": 7, "id": 14, "timestamp": 2},
        {"field": 8, "id": 16, "timestamp": 2},
        {"field": 9, "id": 18, "timestamp": 2},
        {"field": 10, "id": 20, "timestamp": 2},
    ]

    response = _request(0, False, None)
    next_cursor = decode_cursor(response).next
    position = 0

    while next_cursor:
        assert (
            expected_result[position: position + len(response.data['results'])] == response.data['results']
        )
        position += len(response.data['results'])
        response = _request(*next_cursor)
        next_cursor = decode_cursor(response).next

    prev_cursor = decode_cursor(response).prev
    position = 20

    while prev_cursor:
        assert (
            expected_result[position - len(response.data['results']): position] == response.data['results']
        )
        position -= len(response.data['results'])
        response = _request(*prev_cursor)
        prev_cursor = decode_cursor(response).prev
