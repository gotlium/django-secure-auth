# -*- coding: utf-8 -*-

from django.views.generic.edit import FormView
try:
    from django.core.urlresolvers import reverse
except ImportError:
    from django.urls import reverse
from django.shortcuts import HttpResponseRedirect, Http404

from registration.models import RegistrationProfile, SHA1_RE
from registration.backends.default import views

from secureauth.forms import ActivatePhoneForm, CodeForm
from secureauth.defaults import SMS_AGE, SMS_FORCE
from secureauth.models import UserAuthPhone
from secureauth.utils.sign import Sign


def _get_user(**kwargs):
    try:
        activation_key = kwargs.get('activation_key')
        if SHA1_RE.search(activation_key):
            return RegistrationProfile.objects.get(
                activation_key=activation_key).user
    except RegistrationProfile.DoesNotExist:
        pass


class CheckKeyMixin(object):
    def get(self, request, *args, **kwargs):
        user = _get_user(**kwargs)
        if user is None:
            return HttpResponseRedirect(
                reverse('registration_activation_failed')
            )
        return super(CheckKeyMixin, self).get(request, *args, **kwargs)


class ActivationView(CheckKeyMixin, FormView):
    template_name = 'secureauth/registration_confirm.html'
    form_class = ActivatePhoneForm

    def form_valid(self, form):
        user = _get_user(**self.kwargs)
        if user is not None:
            UserAuthPhone.objects.filter(user=user).delete()
            phone = UserAuthPhone(
                enabled=False, user=user, phone=form.cleaned_data.get('phone'))
            phone.save()
            phone.send_sms()
        return super(ActivationView, self).form_valid(form)

    def get_success_url(self):
        return reverse('registration_confirm', kwargs=self.kwargs)


class ConfirmView(CheckKeyMixin, FormView):
    template_name = 'secureauth/registration_confirm.html'
    form_class = CodeForm

    def get_form(self, form_class=None):
        return form_class(
            _get_user(**self.kwargs), UserAuthPhone, **self.get_form_kwargs()
        )

    def form_valid(self, form):
        return super(ConfirmView, self).form_valid(form)

    def get_success_url(self):
        key = Sign().sign(self.kwargs.get('activation_key'))
        return reverse(
            'registration_activation_done', kwargs=self.kwargs
        ) + '?key=' + key


class ActivationDoneView(CheckKeyMixin, views.ActivationView):
    def activate(self, request, activation_key):
        sign_key = Sign().unsign(request.GET.get('key'), SMS_AGE * 2)
        if str(activation_key) != str(sign_key):
            raise Http404('Not found!')

        obj = super(ActivationDoneView, self).activate(request, activation_key)
        if obj is not None:
            UserAuthPhone.objects.filter(user=obj).update(enabled=1)
        return obj

    @staticmethod
    def get_success_url(*args, **kwargs):
        return 'registration_activation_complete_view', (), {}


ActivationView = ActivationView if SMS_FORCE else views.ActivationView
