# -*- encoding: utf-8 -*-

from django.views.decorators.cache import never_cache
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.admin.sites import AdminSite
from django.utils.translation import ugettext

from secureauth.auth_forms import BaseAuthForm
from secureauth.views import login


class SecureAuthAdminSite(AdminSite):
    login_form = BaseAuthForm
    login_template = "secureauth/admin_login.html"
    password_change_template = "secureauth/admin_password_change_form.html"

    @never_cache
    def login(self, request, extra_context=None):
        context = {
            'title': ugettext('Log in'),
            'app_path': request.get_full_path(),
            REDIRECT_FIELD_NAME: request.get_full_path(),
        }
        context.update(extra_context or {})

        defaults = {
            'extra_context': context,
            'current_app': self.name,
            'authentication_form': self.login_form,
            'template_name': self.login_template,
            'redirect_to': request.get_full_path(),
        }
        return login(request, **defaults)


site = SecureAuthAdminSite()
