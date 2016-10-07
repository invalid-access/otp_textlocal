from __future__ import absolute_import, division, print_function, unicode_literals

import django.conf
import django.test.utils


class Settings(object):
    """
    This is a simple class to take the place of the global settings object. An
    instance will contain all of our settings as attributes, with default
    values if they are not specified by the configuration.
    """
    _defaults = {
        'OTP_TEXTLOCAL_ACCOUNT': None,
        'OTP_TEXTLOCAL_AUTH': None,
        'OTP_TEXTLOCAL_CHALLENGE_MESSAGE': "Sent by SMS",
        'OTP_TEXTLOCAL_FROM': None,
        'OTP_TEXTLOCAL_NO_DELIVERY': False,
        'OTP_TEXTLOCAL_TOKEN_TEMPLATE': '{token}',
        'OTP_TEXTLOCAL_TOKEN_VALIDITY': 30,
    }

    def __getattr__(self, name):
        if hasattr(django.conf.settings, name):
            value = getattr(django.conf.settings, name)
        elif name in self._defaults:
            value = self._defaults[name]
        else:
            raise AttributeError(name)

        return value


settings = Settings()
