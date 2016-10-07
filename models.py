from __future__ import absolute_import, division, print_function, unicode_literals

from binascii import unhexlify
import logging
import requests
import time

from django.core.exceptions import ImproperlyConfigured
from django.db import models

from django_otp.models import Device
from django_otp.oath import TOTP
from django_otp.util import random_hex, hex_validator

from .conf import settings


logger = logging.getLogger(__name__)


def default_key():
    return random_hex(20)


def key_validator(value):
    return hex_validator(20)(value)


class TextlocalSMSDevice(Device):
    """
    A :class:`~django_otp.models.Device` that delivers codes via the Textlocal SMS
    service. This uses TOTP to generate temporary tokens, which are valid for
    :setting:`OTP_TEXTLOCAL_TOKEN_VALIDITY` seconds. Once a given token has been
    accepted, it is no longer valid, nor is any other token generated at an
    earlier time.

    .. attribute:: number

        *CharField*: The mobile phone number to deliver to.

    .. attribute:: key

        *CharField*: The secret key used to generate TOTP tokens.

    .. attribute:: last_t

        *BigIntegerField*: The t value of the latest verified token.

    """
    number = models.CharField(
        max_length=16,
        help_text="The mobile number to deliver tokens to."
    )

    key = models.CharField(
        max_length=40,
        validators=[key_validator],
        default=default_key,
        help_text="A random key used to generate tokens (hex-encoded)."
    )

    last_t = models.BigIntegerField(
        default=-1,
        help_text="The t value of the latest verified token. The next token must be at a higher time step."
    )

    class Meta(Device.Meta):
        verbose_name = "Textlocal SMS Device"

    @property
    def bin_key(self):
        return unhexlify(self.key.encode())

    def generate_challenge(self):
        """
        Sends the current TOTP token to ``self.number``.

        :returns: :setting:`OTP_TEXTLOCAL_CHALLENGE_MESSAGE` on success.
        :raises: Exception if delivery fails.

        """
        totp = self.totp_obj()
        token = format(totp.token(), '06d')
        message = settings.OTP_TEXTLOCAL_TOKEN_TEMPLATE.format(token=token)

        if settings.OTP_TEXTLOCAL_NO_DELIVERY:
            logger.info(message)
        else:
            self._deliver_token(message)

        challenge = settings.OTP_TEXTLOCAL_CHALLENGE_MESSAGE.format(token=token)

        return challenge

    def _deliver_token(self, token):
        self._validate_config()

        url = settings.OTP_TEXTLOCAL_URL #'https://api.textlocal.com/2010-04-01/Accounts/{0}/SMS/Messages.json'.format(settings.OTP_TEXTLOCAL_API_KEY)
        data = {
            'sender': settings.OTP_TEXTLOCAL_SENDER,
            'message': str(token),
            'numbers': self.number,
            'apiKey': settings.OTP_TEXTLOCAL_API_KEY,
        }
        #{
        #
        #    'From': settings.OTP_TEXTLOCAL_SENDER,
        #    'To': self.number,
        #    'Body': str(token),
        #}

        response = requests.post(url, data=data)

        try:
            response.raise_for_status()
        except Exception as e:
            logger.exception('Error sending token by Textlocal SMS: {0}'.format(e))
            raise

        json_response = response.json()

        if ('status' not in json_response) or json_response['status'] != 'success':
            message = str(json_response)
            logger.error('Error sending token by Textlocal SMS: {0}'.format(message))
            raise Exception(message)

    def _validate_config(self):
        if settings.OTP_TEXTLOCAL_API_KEY is None:
            raise ImproperlyConfigured('OTP_TEXTLOCAL_API_KEY must be set to your Textlocal API KEY')

        if settings.OTP_TEXTLOCAL_URL is None:
            raise ImproperlyConfigured('OTP_TEXTLOCAL_URL must be set to the Textlocal send-msg API endpoint URL')

        if settings.OTP_TEXTLOCAL_SENDER is None:
            raise ImproperlyConfigured('OTP_TEXTLOCAL_SENDER must be set to one of your Textlocal sender (based on mask)')

    def verify_token(self, token):
        try:
            token = int(token)
        except Exception:
            verified = False
        else:
            totp = self.totp_obj()
            tolerance = settings.OTP_TEXTLOCAL_TOKEN_VALIDITY

            for offset in range(-tolerance, 1):
                totp.drift = offset
                if (totp.t() > self.last_t) and (totp.token() == token):
                    self.last_t = totp.t()
                    self.save()

                    verified = True
                    break
            else:
                verified = False

        return verified

    def totp_obj(self):
        totp = TOTP(self.bin_key, step=1)
        totp.time = time.time()

        return totp
