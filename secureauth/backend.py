# -*- coding: utf-8 -*-

try:
    from django.db.models import get_model
except ImportError:
    from django.apps.apps import get_model
from django.contrib.auth import authenticate


class AuthBackend(object):
    def auth(self, credentials, method='', code=''):
        user = authenticate(**credentials)
        auth_backend = get_model('secureauth', 'UserAuth%s' % method)

        if auth_backend is not None and user is not None:
            if auth_backend.objects.filter(user=user).exists():
                auth_backend = auth_backend.objects.get(user=user)
                if auth_backend.check_auth_code(code) is True:
                    auth_backend.update_last_verified()
                    user.backend = 'django.contrib.auth.backends.ModelBackend'
                    return user
        return None
