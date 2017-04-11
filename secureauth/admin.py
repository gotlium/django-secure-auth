# -*- encoding: utf-8 -*-

from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
try:
    from django.core.urlresolvers import reverse
except ImportError:
    from django.urls import reverse
from django.contrib import admin

from secureauth.defaults import ENABLE_ADMIN_LINKS


class CustomUserAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ('secure_auth',)

    def secure_auth(self, obj):
        url1 = reverse('disable_methods', args=[obj.pk])
        url2 = reverse('unban_ip')
        return '<a href="%s">methods</a>/<a href="%s">ip</a>' % (url1, url2)

    secure_auth.allow_tags = True
    secure_auth.short_description = 'Secure auth'


if ENABLE_ADMIN_LINKS is True:
    admin.site.unregister(User)
    admin.site.register(User, CustomUserAdmin)
