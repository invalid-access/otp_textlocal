from __future__ import absolute_import, division, print_function, unicode_literals

from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered

from .models import TextlocalSMSDevice


class TextlocalSMSDeviceAdmin(admin.ModelAdmin):
    """
    :class:`~django.contrib.admin.ModelAdmin` for
    :class:`~otp_textlocal.models.TextlocalSMSDevice`.
    """
    fieldsets = [
        ('Identity', {
            'fields': ['user', 'name', 'confirmed'],
        }),
        ('Configuration', {
            'fields': ['number', 'key'],
        }),
    ]
    raw_id_fields = ['user']


try:
    admin.site.register(TextlocalSMSDevice, TextlocalSMSDeviceAdmin)
except AlreadyRegistered:
    # Ignore the useless exception from multiple imports
    pass
