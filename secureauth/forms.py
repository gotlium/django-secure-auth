# -*- coding: utf-8 -*-

from django.utils.translation import ugettext_lazy as _
from django import forms

from models import UserAuthNotification
from utils.sign import Sign


class BasicForm(forms.Form):
    enabled = forms.BooleanField(label=_('Enabled'), required=False)

    def decrypt(self, key, *args):
        if len(args) > 2 and args[2] and key in args[2]:
            unsigned = Sign().unsign(args[2][key])
            if unsigned is not None:
                args[2][key] = unsigned

    def __init__(self, user, model, *args, **kwargs):
        self.user = user
        self.model = model
        super(BasicForm, self).__init__(*args, **kwargs)

    def save(self):
        if not self.user:
            return None

        try:
            data = self.model.objects.get(user=self.user)
        except self.model.DoesNotExist:
            data = self.model(user=self.user)

        return data


class CodeForm(forms.Form):
    code = forms.CharField(label=_('Code'), required=True)

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
        self.decrypt('phone', *args)
        super(PhoneBasicForm, self).__init__(*args, **kwargs)

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone and not phone.startswith('+') or ' ' in phone:
            raise forms.ValidationError(
                _('Phone does not contain spaces and must be starts with a +'))
        return phone

    def save(self):
        model = super(PhoneBasicForm, self).save()
        model.phone = self.cleaned_data.get('phone')
        model.save()
        return model


class QuestionForm(BasicForm):
    question = forms.CharField(label=_('Question'), required=True)
    code = forms.CharField(label=_('code'), required=True, max_length=16)

    def __init__(self, *args, **kwargs):
        self.decrypt('code', *args)
        self.decrypt('question', *args)
        super(QuestionForm, self).__init__(*args, **kwargs)
        if args[2] and args[2].get('code'):
            self.fields['code'].widget = forms.HiddenInput()
        self.fields['code'].label = _('Answer')

    def save(self):
        model = super(QuestionForm, self).save()
        return model.set_data(
            self.cleaned_data.get('question'), self.cleaned_data.get('code'))


class NotificationForm(forms.ModelForm):
    class Meta:
        model = UserAuthNotification
        exclude = ('user',)


class ActivatePhoneForm(forms.Form):
    phone = forms.CharField(label=_('Phone'), required=True, max_length=16)

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone.startswith('+') or ' ' in phone:
            raise forms.ValidationError(
                _('Phone does not contain spaces and must be starts with a +'))
        return phone
