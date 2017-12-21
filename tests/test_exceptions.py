from __future__ import unicode_literals

from django.test import TestCase
from django.utils import six, translation
from django.utils.translation import ugettext_lazy as _

from rest_framework.exceptions import (
    APIException, ErrorDetail, Throttled, _get_error_details
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
            'message': 'Request was throttled. Expected available in {} seconds.'.format(2 if six.PY3 else 2.),
            'code': 'throttled'}

        exception = Throttled(wait=2, detail='Slow down!')
        assert exception.get_full_details() == {
            'message': 'Slow down! Expected available in {} seconds.'.format(2 if six.PY3 else 2.),
            'code': 'throttled'}


class TranslationTests(TestCase):

    @translation.override('fr')
    def test_message(self):
        # this test largely acts as a sanity test to ensure the translation files are present.
        self.assertEqual(_('A server error occurred.'), 'Une erreur du serveur est survenue.')
        self.assertEqual(six.text_type(APIException()), 'Une erreur du serveur est survenue.')
