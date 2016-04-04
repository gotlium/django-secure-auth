# -*- coding: utf-8 -*-

from django.utils.translation import ugettext_lazy as _
from django.forms.models import inlineformset_factory
from django.test.client import RequestFactory
from django import forms

from secureauth.models import (
    UserAuthNotification, UserAuthLogging, UserAuthToken, UserAuthAttempt,
    UserAuthCode, UserAuthPhone, UserAuthQuestion, UserAuthIP, UserAuthIPRange)
from secureauth.defaults import CHECK_PASSWORD, INPUT_TYPE
from secureauth.utils.sign import Sign
from secureauth.utils import is_phone


class BasicForm(forms.Form):
    enabled = forms.BooleanField(label=_('Enabled'), required=False)

    @staticmethod
    def decrypt(key, **kwargs):
        if 'initial' in kwargs:
            if kwargs['initial'] and key in kwargs['initial'].keys():
                unsigned = Sign().unsign(kwargs['initial'][key])
                if unsigned is not None:
                    kwargs['initial'][key] = unsigned

    def __init__(self, request, model, *args, **kwargs):
        self.request = request
        self.user = request.user
        self.model = model
        super(BasicForm, self).__init__(*args, **kwargs)

        if CHECK_PASSWORD is True:
            self.fields['current_password'] = forms.CharField(
                label=_('Current password:'), widget=forms.PasswordInput)

    def hide_field(self, model_class, field_name):
        try:
            model_class.objects.get(user=self.request.user)
            self.fields.pop(field_name)
        except model_class.DoesNotExist:
            pass

    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password', '')
        if not self.request.user.check_password(current_password):
            raise forms.ValidationError(_(u'Invalid password'))

    def save(self):
        if not self.user:
            return None

        try:
            data = self.model.objects.get(user=self.user)
        except self.model.DoesNotExist:
            data = self.model(user=self.user)

        return data


class CodeForm(forms.Form):
    code = forms.CharField(
        label=_('Code'), required=True,
        widget=forms.TextInput(attrs={
            'autocomplete': 'off', 'type': INPUT_TYPE
        }))

    def __init__(self, user, model, *args, **kwargs):
        self.user = user
        self.model = model
        super(CodeForm, self).__init__(*args, **kwargs)

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if code and self.user and self.model:
            obj = self.model.objects.get(user=self.user)
            if obj.check_auth_code(self.cleaned_data.get('code'), True):
                return code
        raise forms.ValidationError(_('Entered code is wrong'))

    def save(self):
        if self.user:
            data = self.model.objects.get(user=self.user)
            data.enabled = True
            data.save()
            return data


class PhoneBasicForm(BasicForm):
    phone = forms.CharField(label=_('Phone'), required=True, max_length=16)

    def __init__(self, *args, **kwargs):
        super(PhoneBasicForm, self).__init__(*args, **kwargs)
        self.hide_field(UserAuthPhone, 'phone')

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone and not phone.startswith('+') or ' ' in phone:
            raise forms.ValidationError(
                _('Phone does not contain spaces and must be starts with a +'))
        elif not is_phone(phone):
            raise forms.ValidationError(
                _('The phone number entered is not valid'))
        return phone

    def save(self):
        model = super(PhoneBasicForm, self).save()
        model.phone = self.cleaned_data.get('phone')
        model.save()
        return model


class QuestionForm(BasicForm):
    question = forms.CharField(label=_('Question'), required=True)
    code = forms.CharField(label=_('code'), required=True, max_length=16)

    def __init__(self, request, *args, **kwargs):
        # self.decrypt('code', **kwargs)
        # self.decrypt('question', **kwargs)
        super(QuestionForm, self).__init__(request, *args, **kwargs)

        self.fields['code'].label = _('Answer')

        self.hide_field(UserAuthQuestion, 'code')
        self.hide_field(UserAuthQuestion, 'question')

    def save(self):
        model = super(QuestionForm, self).save()
        return model.set_data(
            self.cleaned_data.get('question'), self.cleaned_data.get('code'))


class BaseSettingsForm(forms.ModelForm):
    enabled = forms.BooleanField(label=_('Enabled'), required=False)

    def __init__(self, request, *args, **kwargs):
        self.request = request

        super(BaseSettingsForm, self).__init__(*args, **kwargs)

        if CHECK_PASSWORD is True:
            self.fields['current_password'] = forms.CharField(
                label=_('Current password:'), widget=forms.PasswordInput)

    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password', '')
        if not self.request.user.check_password(current_password):
            raise forms.ValidationError(_(u'Invalid password'))


class NotificationForm(BaseSettingsForm):
    class Meta:
        model = UserAuthNotification
        exclude = ('user',)


class LoggingForm(BaseSettingsForm):
    class Meta:
        model = UserAuthLogging
        exclude = ('user',)


class IPSettingsForm(BaseSettingsForm):
    class Meta:
        model = UserAuthIP
        exclude = ('user',)


class ActivatePhoneForm(forms.Form):
    phone = forms.CharField(label=_('Phone'), required=True, max_length=16)

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone.startswith('+') or ' ' in phone:
            raise forms.ValidationError(
                _('Phone does not contain spaces and must be starts with a +'))
        elif not is_phone(phone):
            raise forms.ValidationError(
                _('The phone number entered is not valid'))
        return phone


class DisableMethodForm(forms.Form):
    code = forms.BooleanField(label=_('Codes Auth'), required=False)
    token = forms.BooleanField(label=_('TOTP Auth'), required=False)
    phone = forms.BooleanField(label=_('SMS Auth'), required=False)
    question = forms.BooleanField(label=_('Question Auth'), required=False)
    ip = forms.BooleanField(label=_('IP Auth'), required=False)

    current_password = forms.CharField(
        label=_('Current password:'), widget=forms.PasswordInput)

    def __init__(self, request, pk, *args, **kwargs):
        self._request = request
        self._pk = pk

        def get_status(model):
            return model.objects.filter(user_id=self._pk, enabled=1).exists()

        kwargs['initial'] = {
            'code': get_status(UserAuthCode),
            'token': get_status(UserAuthToken),
            'phone': get_status(UserAuthPhone),
            'question': get_status(UserAuthQuestion),
            'ip': get_status(UserAuthIP),
        }
        super(DisableMethodForm, self).__init__(*args, **kwargs)

    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password', '')
        if not self._request.user.check_password(current_password):
            raise forms.ValidationError(_(u'Invalid password'))

    def save(self):
        def set_status(model, key):
            model.objects.filter(user_id=self._pk).update(
                enabled=self.cleaned_data.get(key, False))

        set_status(UserAuthCode, 'code')
        set_status(UserAuthToken, 'token')
        set_status(UserAuthPhone, 'phone')
        set_status(UserAuthQuestion, 'question')
        set_status(UserAuthIP, 'ip')


class IpBanForm(forms.Form):
    ip = forms.CharField(label=_('IP Address:'), required=True, max_length=16)

    def save(self):
        request = RequestFactory().get('/')
        request.META['REMOTE_ADDR'] = self.cleaned_data.get('ip')
        UserAuthAttempt.remove(request)


IPRangeFormSet = inlineformset_factory(
    UserAuthIP, UserAuthIPRange, exclude=('ip',))
