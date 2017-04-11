# coding=utf-8;

from django.http import (
    HttpResponseRedirect, Http404, HttpResponse, HttpResponseBadRequest)
from django.utils.translation import ugettext as _
from django.template.response import TemplateResponse
from django.utils.http import is_safe_url
from django.shortcuts import render
from django.contrib.auth import REDIRECT_FIELD_NAME, login as auth_login
from django.contrib.sites.models import get_current_site
from django.shortcuts import redirect
try:
    from django.core.urlresolvers import reverse
except ImportError:
    from django.urls import reverse
from django.contrib import messages
from django.conf import settings
from django.views.generic import View, TemplateView, FormView
from django_tables2 import RequestConfig

from secureauth.auth_forms import get_available_auth_methods
from secureauth.auth_forms import ConfirmAuthenticationForm
from secureauth.auth_forms import BaseAuthForm
from secureauth.utils.sign import Sign
from secureauth.filters import UserAuthActivityFilter
from secureauth.tables import UserAuthActivityTable
from secureauth.utils.decorators import (
    AjaxDecoratorMixin, AuthDecoratorMixin, StaffDecoratorMixin,
    login_decorator)
from secureauth.utils import get_ip, get_data
from secureauth.forms import (
    CodeForm, PhoneBasicForm, QuestionForm,
    NotificationForm, LoggingForm, DisableMethodForm,
    IpBanForm, IPSettingsForm, IPRangeFormSet)
from secureauth.models import (
    UserAuthIP, UserAuthIPRange,
    UserAuthPhone, UserAuthCode, UserAuthQuestion, UserAuthToken,
    UserAuthActivity, UserAuthNotification, UserAuthAttempt, UserAuthLogging)
from secureauth.defaults import SMS_FORCE, CHECK_ATTEMPT
from secureauth.views.base import (
    SecureAuthBasicView, SettingsView, AjaxViewMixin
)


@login_decorator
def login(request, template_name='secureauth/login.html',
          redirect_field_name=REDIRECT_FIELD_NAME,
          authentication_form=BaseAuthForm,
          current_app=None, extra_context=None, redirect_to=''
          ):  # pylint: disable=R0913
    redirect_to = request.REQUEST.get(redirect_field_name, redirect_to)

    if CHECK_ATTEMPT and UserAuthAttempt.is_banned(request):
        return HttpResponseBadRequest()

    if request.method == "POST":
        form = authentication_form(
            request, data=request.POST, test_cookie_enabled=False)
        if form.is_valid():
            if not is_safe_url(url=redirect_to, host=request.get_host()):
                redirect_to = settings.LOGIN_REDIRECT_URL
                if '/' not in redirect_to and '.' not in redirect_to:
                    redirect_to = reverse(settings.LOGIN_REDIRECT_URL)

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

                if request.session.test_cookie_worked():
                    request.session.delete_test_cookie()

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
                       extra_context=None, current_app=None
                       ):  # pylint: disable=R0913
    if CHECK_ATTEMPT and UserAuthAttempt.is_banned(request):
        return HttpResponseBadRequest()

    data = get_data(request)
    if extra_context is None and data.get('extra_context'):
        extra_context = data.get('extra_context')

    if hasattr(request, 'user') and request.user.is_authenticated():
        return HttpResponseRedirect(data.get('redirect_to', '/'))
    elif request.method == "POST":
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


class PhoneSendSmsView(AjaxViewMixin, AjaxDecoratorMixin, View):
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        user = self.get_user_or_404(UserAuthPhone)
        user.send_sms()
        return HttpResponse(_('SMS was sent!'))


class CodeGetRandomView(AjaxViewMixin, AjaxDecoratorMixin, View):
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        user = self.get_user_or_404(UserAuthCode)
        return HttpResponse(
            _('Enter %d code from code saved code list')
            % user.get_code_number())


class GetQuestionView(AjaxViewMixin, AjaxDecoratorMixin, View):
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        user = self.get_user_or_404(UserAuthQuestion)
        return HttpResponse(user.get_question())


class AuthSettingsView(AuthDecoratorMixin, View):
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        if UserAuthLogging.is_enabled(request):
            UserAuthActivity.check_location(request)
        return render(request, 'secureauth/settings.html')


class TotpSettingsView(SecureAuthBasicView):
    view = 'totp_settings'
    model = UserAuthToken


class PhoneSettingsView(SecureAuthBasicView):
    view = 'phone_settings'
    model = UserAuthPhone
    forms = [PhoneBasicForm, CodeForm]


class CodesSettingsView(SecureAuthBasicView):
    view = 'codes_settings'
    model = UserAuthCode


class SendCodesView(AuthDecoratorMixin, View):
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        if request.session.get('step') != 3:
            raise Http404
        elif UserAuthCode.send_codes(request):
            messages.info(request, _('Codes were sent to the email'))
            UserAuthNotification.notify(
                request, _('Codes were sent to the email'))
            if request.session.get('step'):
                del request.session['step']
        return redirect('codes_settings')


class QuestionSettingsView(SecureAuthBasicView):
    view = 'question_settings'
    model = UserAuthQuestion
    forms = [QuestionForm, CodeForm]


class AuthActivityView(AuthDecoratorMixin, TemplateView):
    http_method_names = ['get']
    template_name = 'secureauth/auth_activity.html'

    def get_context_data(self, **kwargs):
        context = super(AuthActivityView, self).get_context_data(**kwargs)

        queryset = UserAuthActivity.objects.filter(user=self.request.user)
        queryset = UserAuthActivityFilter(self.request.GET, queryset=queryset)
        table = UserAuthActivityTable(queryset, request=self.request)
        RequestConfig(self.request).configure(table)
        context.update({
            'table': table,
            'filter': queryset
        })
        return context


class NotifySettingsView(SettingsView):
    view = 'notify_settings'
    model = UserAuthNotification
    form = NotificationForm


class LoggingSettingsView(SettingsView):
    view = 'logging_settings'
    model = UserAuthLogging
    form = LoggingForm


class IpSettingsView(SettingsView):
    view = 'ip_settings'
    model = UserAuthIP
    form = IPSettingsForm
    form_set = IPRangeFormSet


class DisableMethodsView(StaffDecoratorMixin, FormView):
    template_name = 'secureauth/admin_disable_methods.html'
    form_class = DisableMethodForm

    def get_form_kwargs(self):
        kwargs = super(DisableMethodsView, self).get_form_kwargs()
        kwargs.update({
            'request': self.request,
            'pk': self.kwargs.get('pk')
        })
        return kwargs

    def form_valid(self, form):
        messages.info(self.request, _('Successfully saved'))
        form.save()
        return redirect('disable_methods', self.kwargs.get('pk'))

    def get_context_data(self, **kwargs):
        context = super(DisableMethodsView, self).get_context_data(**kwargs)
        context.update({
            'pk': self.kwargs.get('pk')
        })
        return context


class UnbanIpView(StaffDecoratorMixin, FormView):
    template_name = 'secureauth/admin_ban_ip.html'
    form_class = IpBanForm

    def form_valid(self, form):
        messages.info(self.request, _('Successfully saved'))
        form.save()
        return redirect('unban_ip')
