# coding=utf-8;
import time
import datetime

from django.views.generic import FormView, TemplateView
from django.http import Http404
from django.utils.translation import ugettext as _
from django.forms.models import model_to_dict
from django.shortcuts import redirect
try:
    from django.core.urlresolvers import reverse
except ImportError:
    from django.urls import reverse
from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured

from secureauth.utils import get_ip
from secureauth.models import UserAuthNotification
from secureauth.defaults import SMS_FORCE

__all__ = ['SettingsRunner', 'ConfigureRunner', 'DisabledRunner',
           'DoneRunner', 'OneStepSettingsRunner']


class BasicRunnerMixin(object):
    view = None
    model = None
    obj = None
    forms = None
    class_name_view = ''

    def _url(self, step):
        return '%s?step=%d' % (reverse(self.view), step)

    def _redirect(self, step):
        self._set_next_step(step)
        return redirect(self._url(step))

    def _set_next_step(self, step):
        now = datetime.datetime.now()
        self.request.session['step'] = step
        self.request.session['step_time'] = time.mktime(now.timetuple())
        if not self.request.session.get('ip'):
            self.request.session['ip'] = get_ip(self.request)

    def get_template_names(self):
        return ['secureauth/{view}/{class_view}.html'.format(
            view=self.view, class_view=self._get_class_view())]

    def _get_class_view(self):
        if not self.class_name_view:
            raise ImproperlyConfigured(_('Class name should be set'))
        return self.class_name_view


class SettingsRunner(BasicRunnerMixin, FormView):
    class_name_view = 'settings'

    def get(self, *args, **kwargs):
        self._cleanup_if_not_enabled()
        return super(SettingsRunner, self).get(*args, **kwargs)

    def _cleanup_if_not_enabled(self):
        if self.request.method == 'GET':
            objs = self.model.objects.filter(
                user=self.request.user, enabled=False)
            if objs.exists():
                objs.delete()
                self.obj = None

    def get_form_class(self):
        return self.forms[0]

    def form_valid(self, form):
        form_enabled = form.cleaned_data.get('enabled')
        if self.obj and self.obj.enabled and form_enabled:
            messages.info(self.request, _('Nothing to save'))
            return self._redirect(1)
        elif form_enabled is True:
            return self.settings_enable(form)
        else:
            return self.settings_remove()

    def settings_enable(self, form):
        self.obj and self.obj.delete()
        model = form.save()
        model.enabled = False
        model.make()
        return self._redirect(2)

    def settings_remove(self):
        step = 4 if self.obj else 1

        if SMS_FORCE is True and self.view == 'phone_settings':
            messages.info(
                self.request, _('Default backend can not be removed'))
            return self._redirect(1)

        self.obj and self.obj.delete()
        UserAuthNotification.notify(
            self.request, _('Auth method was disabled'))
        return self._redirect(step)

    def get_form_kwargs(self):
        kwargs = super(SettingsRunner, self).get_form_kwargs()
        kwargs.update({
            'request': self.request,
            'model': self.model
        })
        return kwargs

    def get_initial(self):
        if self.obj and self.request.method == 'GET':
            return model_to_dict(self.obj)


class ConfigureRunner(BasicRunnerMixin, FormView):
    class_name_view = 'configure'

    def get_form_class(self):
        return self.forms[1]

    def get_form_kwargs(self):
        kwargs = super(ConfigureRunner, self).get_form_kwargs()
        kwargs.update({
            'user': self.request.user,
            'model': self.model
        })
        return kwargs

    def form_valid(self, form):
        form.save()
        UserAuthNotification.notify(
            self.request, _('New Auth method was enabled'))
        return self._redirect(3)

    def get_context_data(self, **kwargs):
        kwargs = super(ConfigureRunner, self).get_context_data(**kwargs)
        kwargs.update({
            'personal_data': self.get_object().get_data(),
        })
        return kwargs

    def get_object(self, *args, **kwargs):
        if not self.obj:
            raise Http404(_('Setting disabled'))
        return self.obj


class DisabledRunner(BasicRunnerMixin, TemplateView):
    class_name_view = 'was_disabled'

    def post(self, *args, **kwargs):
        return self.get(*args, **kwargs)


class DoneRunner(BasicRunnerMixin, TemplateView):
    class_name_view = 'was_done'

    def post(self, *args, **kwargs):
        return self.get(*args, **kwargs)


class OneStepSettingsRunner(FormView):
    form_class = None
    view = None
    obj = None
    model = None
    form_set = None

    def get_object(self, *args, **kwargs):
        if not self.obj:
            raise Http404(_('Setting disabled'))
        return self.obj

    def form_valid(self, form):
        form_set = self.get_form_set()
        form.save(commit=False)
        form.user = self.request.user
        instance = form.save()
        if form_set is not None and form_set.is_valid():
            form_set.instance = instance
            form_set.save()
        messages.info(self.request, _('Successfully saved'))
        if not form.cleaned_data.get('enabled'):
            UserAuthNotification.notify(
                self.request, _('Your settings has changed'), force=True)
        return redirect(self.view)

    def get_form_kwargs(self):
        kwargs = super(OneStepSettingsRunner, self).get_form_kwargs()
        kwargs.update({
            'request': self.request,
            'instance': self.get_object()
        })
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(OneStepSettingsRunner, self).get_context_data(**kwargs)
        context.update({'form_set': self.get_form_set()})
        return context

    def get_form_set(self):
        return self.form_set and self.form_set(
            self.request.POST or None, instance=self.obj)

    def get_template_names(self):
        return ['secureauth/{view}.html'.format(view=self.view)]

