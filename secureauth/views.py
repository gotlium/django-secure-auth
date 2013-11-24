from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.utils.translation import ugettext as _
from django.template.response import TemplateResponse
from django.utils.http import is_safe_url
from django.shortcuts import resolve_url, render
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import authenticate
from django.conf import settings
from django.forms.models import model_to_dict
from django.contrib.auth import REDIRECT_FIELD_NAME, login as auth_login
from django.contrib.sites.models import get_current_site
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.contrib import messages

from secureauth.auth_forms import get_available_auth_methods
from secureauth.auth_forms import ConfirmAuthenticationForm
from secureauth.utils.sign import Sign
from secureauth.filters import UserAuthActivityFilter
from secureauth.tables import UserAuthActivityTable
from secureauth.utils.decorators import ajax_required
from secureauth.forms import (
    BasicForm, CodeForm, PhoneBasicForm, QuestionForm, NotificationForm)
from secureauth.models import (
    UserAuthPhone, UserAuthCode, UserAuthQuestion, UserAuthToken,
    UserAuthActivity, UserAuthNotification)
from secureauth.defaults import SMS_AGE, SMS_FORCE


def _get_data(request):
    data = Sign().unsign(request.GET.get('data'), age=SMS_AGE*2)
    if data is not None:
        user = authenticate(**data.get('credentials'))
        if user is not None and user.is_active:
            if request.META.get('REMOTE_ADDR') == data.get('ip'):
                return data
    raise Http404('Not found')


@sensitive_post_parameters()
@csrf_protect
@never_cache
def login(request, template_name='secureauth/login.html',
          redirect_field_name=REDIRECT_FIELD_NAME,
          authentication_form=AuthenticationForm,
          current_app=None, extra_context=None):
    redirect_to = request.REQUEST.get(redirect_field_name, '')

    if request.method == "POST":
        form = authentication_form(request, data=request.POST)
        if form.is_valid():
            if not is_safe_url(url=redirect_to, host=request.get_host()):
                redirect_to = resolve_url(settings.LOGIN_REDIRECT_URL)

            if request.session.test_cookie_worked():
                request.session.delete_test_cookie()

            user = form.get_user()

            if SMS_FORCE or len(get_available_auth_methods(user)) > 1:
                data = {
                    'redirect_to': redirect_to,
                    'user_pk': user.pk,
                    'credentials': form.cleaned_data,
                    'ip': request.META.get('REMOTE_ADDR'),
                }
                data = Sign().sign(data)
                return HttpResponseRedirect(
                    '%s?data=%s' % (reverse('auth_confirmation'), data))
            else:

                auth_login(request, user)
                return HttpResponseRedirect(redirect_to)
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


@sensitive_post_parameters()
@csrf_protect
@never_cache
def login_confirmation(request, template_name='secureauth/confirmation.html',
                       authentication_form=ConfirmAuthenticationForm,
                       extra_context=None, current_app=None):
    data = _get_data(request)
    if request.method == "POST":
        form = authentication_form(data, request.POST)
        if form.is_valid():
            user = form.get_user()
            if user and data.get('user_pk') == user.pk:
                auth_login(request, user)

                if request.session.test_cookie_worked():
                    request.session.delete_test_cookie()

                UserAuthActivity.check_location(request)
                UserAuthActivity.log_auth(request)
                UserAuthNotification.notify(request)

                return HttpResponseRedirect(data.get('redirect_to'))
            else:
                raise Http404('ERROR')
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


@ajax_required
@never_cache
def phone_send_sms(request):
    data = _get_data(request)
    user = get_object_or_404(UserAuthPhone, user__id=data.get('user_pk'))
    user.send_sms()
    return HttpResponse(_('SMS was sent!'))


@ajax_required
@never_cache
def code_get_random(request):
    data = _get_data(request)
    user = get_object_or_404(UserAuthCode, user__id=data.get('user_pk'))
    return HttpResponse(
        _('Enter %d code from code saved code list') % user.get_code_number())


@ajax_required
@never_cache
def get_question(request):
    data = _get_data(request)
    user = get_object_or_404(UserAuthQuestion, user__id=data.get('user_pk'))
    return HttpResponse(user.get_question())


@login_required
@never_cache
def auth_settings(request):
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
        return getattr(self, self.method_map.get(self.step))()

    def _url(self, step):
        return '%s?step=%d' % (reverse(self.view), step)

    def _render(self):
        if self.form is not None:
            self.context.update({'form': self.form})
        return render(self.request, self.template, self.context)

    def _redirect(self, step):
        return redirect(self._url(step))

    def _get_data(self, model_data=True):
        if model_data and self.obj.exists() and self.request.method == 'GET':
            return model_to_dict(self.obj[0])
        return self.request.method == 'POST' and self.request.POST or None

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
            self.request.user, self.model, self._get_data())
        if self.request.method == 'POST':
            if self.form.is_valid():
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
        # todo: check ip there & referer with key.
        # Do not open this page with GET url
        self.form = self.code_form(
            self.request.user, self.model, self._get_data(False))
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


@login_required
@never_cache
def totp_settings(request):
    view = BasicView(request, UserAuthToken, 'totp_settings')
    return view.get()


@login_required
@never_cache
def phone_settings(request):
    view = BasicView(
        request, UserAuthPhone, 'phone_settings',
        [PhoneBasicForm, CodeForm])
    return view.get()


@login_required
@never_cache
def codes_settings(request):
    view = BasicView(request, UserAuthCode, 'codes_settings')
    return view.get()


@login_required
@never_cache
def question_settings(request):
    view = BasicView(
        request, UserAuthQuestion, 'question_settings',
        [QuestionForm, CodeForm])
    return view.get()


@login_required
@never_cache
def auth_activity(request):
    queryset = UserAuthActivity.objects.select_related().filter(
        user=request.user)
    queryset = UserAuthActivityFilter(request.GET, queryset=queryset)
    table = UserAuthActivityTable(queryset)
    table.paginate(page=request.GET.get('page', 1))
    return render(request, 'secureauth/auth_activity.html', {
        'table': table,
        'filter': queryset
    })


@login_required
@never_cache
def notify_settings(request):
    instance = UserAuthNotification.objects.get_or_create(user=request.user)[0]
    data = request.method == 'POST' and request.POST or model_to_dict(instance)
    form = NotificationForm(data, instance=instance)
    if request.method == 'POST':
        if form.is_valid():
            form.save(commit=False)
            form.user = request.user
            form.save()
            messages.info(request, _('Successfully saved'))
            if not form.cleaned_data.get('enabled'):
                UserAuthNotification.notify(
                    request, _('Notification was disabled'), force=True)
    return render(request, 'secureauth/notify_settings.html', {'form': form})
