# -*- coding: utf-8 -*-

from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import ugettext_lazy as _
from django.db.models import get_model
from django import forms

from defaults import CAPTCHA_ATTEMPT, CAPTCHA_ENABLED
from captcha.fields import CaptchaField
from models import AUTH_TYPES


def get_available_auth_methods(user):
    available = []
    for auth_type in AUTH_TYPES:
        if not auth_type[0]:
            available.append(auth_type)
            continue
        model = get_model('secureauth', 'UserAuth%s' % auth_type[0])
        if model.objects.filter(user=user, enabled=True).exists():
            available.append(auth_type)
    return available


class ConfirmAuthenticationForm(forms.Form):
    auth_type = forms.ChoiceField(
        label=_("Authentication type"),
        initial='token',
        choices=AUTH_TYPES,
        required=True,
    )
    code = forms.CharField(
        label=_("code"),
        widget=forms.TextInput(),
        required=False
    )

    def __init__(self, data, *args, **kwargs):
        self.credentials = data.get('credentials')
        super(ConfirmAuthenticationForm, self).__init__(*args, **kwargs)
        self.fields['auth_type'].choices = get_available_auth_methods(
            data.get('user_pk'))

    def clean(self):
        code = self.cleaned_data.get('code')
        auth_type = self.cleaned_data.get('auth_type')

        if auth_type and code:
            from secureauth.backend import AuthBackend

            backend = AuthBackend()
            self.user_cache = backend.auth(self.credentials, auth_type, code)
            if self.user_cache is None:
                raise forms.ValidationError(_("Please enter correct code"))
            elif not self.user_cache.is_active:
                raise forms.ValidationError(_("This account is inactive"))
        return self.cleaned_data

    def get_user(self):
        return self.user_cache


class AuthForm(AuthenticationForm):
    def __init__(self, request=None, *args, **kwargs):
        super(AuthForm, self).__init__(request, *args, **kwargs)
        if request.session.get('login_attempts', 1) > CAPTCHA_ATTEMPT:
            self.fields['captcha'] = CaptchaField()

    def is_valid(self):
        is_valid = super(AuthForm, self).is_valid()
        if is_valid:
            self.request.session['login_attempts'] = 0
        else:
            self.request.session['login_attempts'] = self.request.session.get(
                'login_attempts', 1) + 1
        return is_valid


BaseAuthForm = AuthForm if CAPTCHA_ENABLED else AuthenticationForm
