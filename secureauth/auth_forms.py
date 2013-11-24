# -*- coding: utf-8 -*-

from django.utils.translation import ugettext_lazy as _
from django.db.models import get_model
from django import forms

AUTH_TYPES = (
    ('', '---'),
    ('code', _('by code')),
    ('token', _('by token')),
    ('phone', _('by sms')),
    ('question', _('by question')),
)


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
                raise forms.ValidationError(_("This account is inactive."))
        return self.cleaned_data

    def get_user(self):
        return self.user_cache
