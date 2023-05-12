from django.test import RequestFactory, TestCase
from django.utils import translation
from django.utils.translation import gettext_lazy as _

from rest_framework.exceptions import (
    APIException, ErrorDetail, Throttled, _get_error_details, bad_request,
    server_error
)


class ExceptionTestCase(TestCase):

    def test_get_error_details(self):

        example = "string"
        lazy_example = _(example)

        assert _get_error_details(lazy_example) == example

        assert isinstance(
            _get_error_details(lazy_example),
            ErrorDetail
        )

        assert _get_error_details({'nested': lazy_example})['nested'] == example

        assert isinstance(
            _get_error_details({'nested': lazy_example})['nested'],
            ErrorDetail
        )

        assert _get_error_details([[lazy_example]])[0][0] == example

        assert isinstance(
            _get_error_details([[lazy_example]])[0][0],
            ErrorDetail
        )

    def test_get_full_details_with_throttling(self):
        exception = Throttled()
        assert exception.get_full_details() == {
            'message': 'Request was throttled.', 'code': 'throttled'}

        exception = Throttled(wait=2)
        assert exception.get_full_details() == {
            'message': 'Request was throttled. Expected available in {} seconds.'.format(2),
            'code': 'throttled'}

        exception = Throttled(wait=2, detail='Slow down!')
        assert exception.get_full_details() == {
            'message': 'Slow down! Expected available in {} seconds.'.format(2),
            'code': 'throttled'}


class ErrorDetailTests(TestCase):

    def test_eq(self):
        assert ErrorDetail('msg') == ErrorDetail('msg')
        assert ErrorDetail('msg', 'code') == ErrorDetail('msg', code='code')

        assert ErrorDetail('msg') == 'msg'
        assert ErrorDetail('msg', 'code') == 'msg'

    def test_ne(self):
        assert ErrorDetail('msg1') != ErrorDetail('msg2')
        assert ErrorDetail('msg') != ErrorDetail('msg', code='invalid')

        assert ErrorDetail('msg1') != 'msg2'
        assert ErrorDetail('msg1', 'code') != 'msg2'

    def test_repr(self):
        assert repr(ErrorDetail('msg1')) == \
            'ErrorDetail(string={!r}, code=None)'.format('msg1')
        assert repr(ErrorDetail('msg1', 'code')) == \
            'ErrorDetail(string={!r}, code={!r})'.format('msg1', 'code')

    def test_str(self):
        assert str(ErrorDetail('msg1')) == 'msg1'
        assert str(ErrorDetail('msg1', 'code')) == 'msg1'

    def test_hash(self):
        assert hash(ErrorDetail('msg')) == hash('msg')
        assert hash(ErrorDetail('msg', 'code')) == hash('msg')


class TranslationTests(TestCase):

    @translation.override('fr')
    def test_message(self):
        # this test largely acts as a sanity test to ensure the translation files are present.
        self.assertEqual(_('A server error occurred.'), 'Une erreur du serveur est survenue.')
        self.assertEqual(str(APIException()), 'Une erreur du serveur est survenue.')


def test_server_error():
    request = RequestFactory().get('/')
    response = server_error(request)
    assert response.status_code == 500
    assert response["content-type"] == 'application/json'


def test_bad_request():
    request = RequestFactory().get('/')
    exception = Exception('Something went wrong — Not used')
    response = bad_request(request, exception)
    assert response.status_code == 400
    assert response["content-type"] == 'application/json'
