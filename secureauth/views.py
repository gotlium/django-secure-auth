# -*- coding: utf-8 -*-

from django.http import (
    HttpResponseRedirect, Http404, HttpResponse, HttpResponseBadRequest)
from django.utils.translation import ugettext as _
from django.template.response import TemplateResponse
from django.utils.http import is_safe_url
from django.shortcuts import render
from django.contrib.auth import authenticate
from django.forms.models import model_to_dict
from django.contrib.auth import REDIRECT_FIELD_NAME, login as auth_login
from django.contrib.sites.models import get_current_site
from django.shortcuts import get_object_or_404, redirect
from django.core.urlresolvers import reverse
from django.utils.timezone import now
from django.contrib import messages
from django.conf import settings

from django_tables2 import RequestConfig

from secureauth.auth_forms import get_available_auth_methods
from secureauth.auth_forms import ConfirmAuthenticationForm
from secureauth.auth_forms import BaseAuthForm
from secureauth.utils.sign import Sign
from secureauth.filters import UserAuthActivityFilter
from secureauth.tables import UserAuthActivityTable
from secureauth.utils.decorators import (
    ajax_decorator, auth_decorator, staff_decorator, login_decorator)
from secureauth.utils import get_ip
from secureauth.forms import (
    BasicForm, CodeForm, PhoneBasicForm, QuestionForm,
    NotificationForm, LoggingForm, DisableMethodForm,
    IpBanForm, IPSettingsForm, IPRangeFormSet)
from secureauth.models import (
    UserAuthIP, UserAuthIPRange,
    UserAuthPhone, UserAuthCode, UserAuthQuestion, UserAuthToken,
    UserAuthActivity, UserAuthNotification, UserAuthAttempt, UserAuthLogging)
from secureauth.defaults import SMS_AGE, SMS_FORCE, CHECK_ATTEMPT


def _get_data(request):
    data = Sign().unsign(request.GET.get('data'), age=SMS_AGE * 2)
    if data is not None and 'credentials' in data:
        if 'captcha' in data['credentials']:
            data['credentials'].pop('captcha')
        user = authenticate(**data['credentials'])
        if user is not None and user.is_active:
            if get_ip(request) == data.get('ip'):
                return data
    raise Http404('Data is not valid!')


@login_decorator
def login(request, template_name='secureauth/login.html',
          redirect_field_name=REDIRECT_FIELD_NAME,
          authentication_form=BaseAuthForm,
          current_app=None, extra_context=None, redirect_to=''):
    redirect_to = request.REQUEST.get(redirect_field_name, redirect_to)

    if CHECK_ATTEMPT and UserAuthAttempt.is_banned(request):
        return HttpResponseBadRequest()

    if request.method == "POST":
        form = authentication_form(request, data=request.POST)
        if form.is_valid():
            if not is_safe_url(url=redirect_to, host=request.get_host()):
                redirect_to = settings.LOGIN_REDIRECT_URL
                if '/' not in redirect_to and '.' not in redirect_to:
                    redirect_to = reverse(settings.LOGIN_REDIRECT_URL)

            if request.session.test_cookie_worked():
                request.session.delete_test_cookie()

            user = form.get_user()

            if UserAuthIPRange.is_blocked(request, user):
                return render(request, 'secureauth/blocked_ip.html')

            if SMS_FORCE or len(get_available_auth_methods(user)) > 1:
                data = {
                    'credentials': form.cleaned_data,
                    'user_pk': user.pk,
                    'ip': get_ip(request),
                    'redirect_to': redirect_to,
                    'extra_context': extra_context,
                }
                data = Sign().sign(data)
                return HttpResponseRedirect(
                    '%s?data=%s' % (reverse('auth_confirmation'), data))
            else:
                auth_login(request, user)
                if UserAuthLogging.is_enabled(request):
                    UserAuthActivity.check_location(request)
                    UserAuthActivity.log_auth(request)
                UserAuthAttempt.remove(request)
                request.session['ip'] = get_ip(request)
                return HttpResponseRedirect(redirect_to)
        elif CHECK_ATTEMPT is True:
            UserAuthAttempt.clean()
            UserAuthAttempt.store(request)
    else:
        form = authentication_form(request)

    request.session.set_test_cookie()

    current_site = get_current_site(request)

    context = {
        'form': form,
        redirect_field_name: redirect_to,
        'site': current_site,
        'site_name': current_site.name,
    }
    if extra_context is not None:
        context.update(extra_context)
    return TemplateResponse(
        request, template_name, context, current_app=current_app)


@login_decorator
def login_confirmation(request, template_name='secureauth/confirmation.html',
                       authentication_form=ConfirmAuthenticationForm,
                       extra_context=None, current_app=None):
    if CHECK_ATTEMPT and UserAuthAttempt.is_banned(request):
        return HttpResponseBadRequest()

    data = _get_data(request)
    if extra_context is None and data.get('extra_context'):
        extra_context = data.get('extra_context')

    if request.method == "POST":
        form = authentication_form(data, request.POST)
        if form.is_valid():
            user = form.get_user()

            if user and data.get('user_pk') == user.pk:
                auth_login(request, user)

                if request.session.test_cookie_worked():
                    request.session.delete_test_cookie()

                if UserAuthLogging.is_enabled(request):
                    UserAuthActivity.check_location(request)
                    UserAuthActivity.log_auth(
                        request, form.cleaned_data.get('auth_type'))

                UserAuthNotification.notify(request)
                UserAuthAttempt.remove(request)
                request.session['ip'] = get_ip(request)

                return HttpResponseRedirect(data.get('redirect_to'))
            else:
                return HttpResponseBadRequest()
        elif CHECK_ATTEMPT is True:
            UserAuthAttempt.clean()
            UserAuthAttempt.store(request)
    else:
        form = authentication_form(data)

    request.session.set_test_cookie()

    current_site = get_current_site(request)

    context = {
        'form': form,
        'site': current_site,
        'site_name': current_site.name,
        'data': request.GET.get('data'),
    }
    if extra_context is not None:
        context.update(extra_context)
    return TemplateResponse(
        request, template_name, context, current_app=current_app)


@ajax_decorator
def phone_send_sms(request):
    data = _get_data(request)
    user = get_object_or_404(UserAuthPhone, user__id=data.get('user_pk'))
    user.send_sms()
    return HttpResponse(_('SMS was sent!'))


@ajax_decorator
def code_get_random(request):
    data = _get_data(request)
    user = get_object_or_404(UserAuthCode, user__id=data.get('user_pk'))
    return HttpResponse(
        _('Enter %d code from code saved code list') % user.get_code_number())


@ajax_decorator
def get_question(request):
    data = _get_data(request)
    user = get_object_or_404(UserAuthQuestion, user__id=data.get('user_pk'))
    return HttpResponse(user.get_question())


@auth_decorator
def auth_settings(request):
    if UserAuthLogging.is_enabled(request):
        UserAuthActivity.check_location(request)
    return render(request, 'secureauth/settings.html')


class BasicView(object):
    method_map = {
        1: 'settings',
        2: 'configure',
        3: 'was_done',
        4: 'was_disabled',
    }

    def __init__(self, request, model, view, forms=None):
        self.template = None
        self.forms = [BasicForm, CodeForm] if forms is None else forms
        self.basic_form = self.forms[0]
        self.code_form = self.forms[1]
        self.view = view
        self.request = request
        self.context = dict()
        self.model = model
        self.step = int(self.request.GET.get('step', 1))
        self.obj = self.model.objects.filter(user=self.request.user)
        self.form = None

    def __set_template(self):
        data = (self.view, self.method_map.get(self.step))
        self.template = 'secureauth/%s/%s.html' % data

    def __do_step(self):
        self.__set_template()
        if self.step > 1:
            self._check_step(self.step)
        return getattr(self, self.method_map.get(self.step))()

    def _url(self, step):
        return '%s?step=%d' % (reverse(self.view), step)

    def _render(self):
        if self.form is not None:
            self.context.update({'form': self.form})
        return render(self.request, self.template, self.context)

    def _redirect(self, step):
        self._set_next_step(step)
        return redirect(self._url(step))

    def _get_initial(self):
        if self.obj.exists() and self.request.method == 'GET':
            return model_to_dict(self.obj[0])

    def _set_next_step(self, step):
        self.request.session['step'] = step
        self.request.session['step_time'] = now()
        if not self.request.session.get('ip'):
            self.request.session['ip'] = get_ip(self.request)

    def _check_step(self, step):
        if self.request.session.get('step') != step:
            raise Http404
        elif self.request.session.get('ip') != get_ip(self.request):
            return Http404
        elif (now() - self.request.session.get('step_time')).seconds > SMS_AGE:
            return Http404

    def settings_remove(self):
        step = 4 if self.obj.exists() else 1

        if SMS_FORCE is True and self.view == 'phone_settings':
            messages.info(
                self.request, _('Default backend can not be removed'))
            return self._redirect(1)

        self.obj.delete()
        UserAuthNotification.notify(
            self.request, _('Auth method was disabled'))
        return self._redirect(step)

    def settings_enable(self):
        self.obj.delete()
        model = self.form.save()
        model.enabled = False
        model.make()
        return self._redirect(2)

    def settings(self):
        self.form = self.basic_form(
            self.request, self.model, self.request.POST or None,
            initial=self._get_initial())
        if self.request.method == 'POST' and self.form.is_valid():
            form_enabled = self.form.cleaned_data.get('enabled')
            if self.obj.exists() and self.obj[0].enabled and form_enabled:
                messages.info(self.request, _('Nothing to save'))
                return self._redirect(1)
            elif form_enabled is True:
                return self.settings_enable()
            else:
                return self.settings_remove()
        return self._render()

    def configure(self):
        self.form = self.code_form(
            self.request.user, self.model, self.request.POST or None)
        if self.request.method == 'POST':
            if self.form.is_valid():
                self.form.save()
                UserAuthNotification.notify(
                    self.request, _('New Auth method was enabled'))
                return self._redirect(3)
        self.context.update({'personal_data': self.obj[0].get_data()})
        return self._render()

    def was_done(self):
        return self._render()

    def was_disabled(self):
        return self._render()

    def get(self):
        return self.__do_step()


@auth_decorator
def totp_settings(request):
    view = BasicView(request, UserAuthToken, 'totp_settings')
    return view.get()


@auth_decorator
def phone_settings(request):
    view = BasicView(
        request, UserAuthPhone, 'phone_settings',
        [PhoneBasicForm, CodeForm])
    return view.get()


@auth_decorator
def codes_settings(request):
    view = BasicView(request, UserAuthCode, 'codes_settings')
    return view.get()


@auth_decorator
def send_codes(request):
    if request.session.get('step') != 3:
        raise Http404
    elif UserAuthCode.send_codes(request):
        messages.info(request, _('Codes were sent to the email'))
        UserAuthNotification.notify(request, _('Codes were sent to the email'))
        if request.session.get('step'):
            del request.session['step']
    return redirect('codes_settings')


@auth_decorator
def question_settings(request):
    view = BasicView(
        request, UserAuthQuestion, 'question_settings',
        [QuestionForm, CodeForm])
    return view.get()


@auth_decorator
def auth_activity(request):
    queryset = UserAuthActivity.objects.filter(user=request.user)
    queryset = UserAuthActivityFilter(request.GET, queryset=queryset)
    table = UserAuthActivityTable(queryset, request=request)
    RequestConfig(request).configure(table)
    return render(request, 'secureauth/auth_activity.html', {
        'table': table,
        'filter': queryset
    })


def _settings_view(request, model_class, form_class, template, redirect_to,
                   form_set=None):
    instance = model_class.objects.get_or_create(user=request.user)[0]
    data = request.POST or None
    form = form_class(request, data, instance=instance)
    form_set = form_set and form_set(request.POST or None, instance=instance)
    if request.method == 'POST' and form.is_valid():
        form.save(commit=False)
        form.user = request.user
        instance = form.save()
        if form_set is not None and form_set.is_valid():
            form_set.instance = instance
            form_set.save()
        messages.info(request, _('Successfully saved'))
        if not form.cleaned_data.get('enabled'):
            UserAuthNotification.notify(
                request, _('Your settings has changed'), force=True)
        return redirect(redirect_to)
    return render(request, template, {'form': form, 'form_set': form_set})


@auth_decorator
def notify_settings(request):
    return _settings_view(
        request, UserAuthNotification, NotificationForm,
        'secureauth/notify_settings.html', 'notify_settings'
    )


@auth_decorator
def logging_settings(request):
    return _settings_view(
        request, UserAuthLogging, LoggingForm,
        'secureauth/logging_settings.html', 'logging_settings'
    )


@auth_decorator
def ip_settings(request):
    return _settings_view(
        request, UserAuthIP, IPSettingsForm,
        'secureauth/ip_settings.html', 'ip_settings', IPRangeFormSet
    )


@staff_decorator
def disable_methods(request, pk):
    form = DisableMethodForm(request, pk, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        messages.info(request, _('Successfully saved'))
        form.save()
        return redirect('disable_methods', pk)
    return render(request, 'secureauth/admin_disable_methods.html', {
        'form': form, 'pk': pk
    })


@staff_decorator
def unban_ip(request):
    form = IpBanForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        messages.info(request, _('Successfully saved'))
        form.save()
        return redirect('unban_ip')
    return render(request, 'secureauth/admin_ban_ip.html', {
        'form': form
    })
