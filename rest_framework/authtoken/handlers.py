from typing import Dict
from calendar import timegm
from jwt import encode
from jwt import decode
from django.conf import settings as django_settings
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now
from rest_framework.settings import api_settings
from rest_framework import exceptions



class JWTHandler:
    """
    creates api specific tokens
    """
    @classmethod
    def encode(cls, payload: Dict, secret=None, algorithm=None, headers=None, json_encoder=None):
        cls.set_expiration(payload)

        _key = secret or django_settings.SECRET_KEY
        _algorithm = algorithm or api_settings.DEFAULT_JWT_ALGORITHM
        return encode(payload=payload, key=_key, algorithm=_algorithm, headers=headers, json_encoder=json_encoder)

    @classmethod
    def decode(cls, token, secret=None, algorithm=None):
        _key = secret or django_settings.SECRET_KEY
        _algorithm = algorithm or api_settings.DEFAULT_JWT_ALGORITHM

        try:
            _payload = decode(jwt=token, key=_key, algorithms=[_algorithm])
        except exceptions.APIException as e:
            raise exceptions.APIException(_(str(e)))

        return _payload

    @classmethod
    def set_expiration(self, payload, _name="exp", _from=None, _duration=None):
        """
        Updates the expiration time of a token.
        """
        _from = _from or now()
        _duration = _duration or api_settings.DEFAULT_JWT_DURATION
        _expiration_time = _from + _duration
        payload[_name] = timegm(_expiration_time.utctimetuple())
