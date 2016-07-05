# -*- coding: utf-8 -*-
from datetime import datetime

from django.http import Http404
from django.views.generic import View
from django.shortcuts import get_object_or_404

from secureauth.utils import get_ip
from secureauth.forms import BasicForm, CodeForm
from secureauth.defaults import SMS_AGE
from secureauth.views.runners import (
    SettingsRunner, ConfigureRunner, DoneRunner,
    DisabledRunner, OneStepSettingsRunner,
)
from secureauth.utils.decorators import AuthDecoratorMixin
from secureauth.utils import get_data


class SecureAuthBasicView(AuthDecoratorMixin, View):
    step_class_map = {
        1: SettingsRunner,
        2: ConfigureRunner,
        3: DoneRunner,
        4: DisabledRunner,
    }

    view = None
    model = None
    step = None
    obj = None
    forms = [BasicForm, CodeForm]

    def dispatch(self, request, *args, **kwargs):
        self.step = self._get_step(request)
        self.obj = self._get_obj(request)
        return super(SecureAuthBasicView, self).dispatch(
            request, *args, **kwargs)

    @staticmethod
    def _get_step(request):
        return int(request.GET.get('step', 1))

    def _get_step_class(self):
        result = self.step_class_map.get(self.step)
        if not result:
            raise Http404()
        return result

    def _get_obj(self, request):
        try:
            return self.model.objects.get(user=request.user)
        except self.model.DoesNotExist:
            return

    def _do_step(self):
        if self.step > 1:
            self._check_step(self.step)
        return self._get_step_class().as_view(
            **self._get_runner_kwargs())(self.request)

    def _get_runner_kwargs(self):
        return dict(
            forms=self.forms, model=self.model, obj=self.obj, view=self.view)

    def _check_step(self, step):
        now = datetime.now()
        step_time = self.request.session.get('step_time', SMS_AGE+10)
        if self.request.session.get('step') != step:
            raise Http404
        elif self.request.session.get('ip') != get_ip(self.request):
            return Http404
        elif (now - datetime.fromtimestamp(step_time)).seconds > SMS_AGE:
            return Http404

    def get(self, *args, **kwargs):
        return self._do_step()

    def post(self, *args, **kwargs):
        return self._do_step()


class SettingsView(SecureAuthBasicView):
    step_class_map = {
        1: OneStepSettingsRunner,
    }

    form = None
    form_set = None

    def _get_runner_kwargs(self):
        return dict(
            form_class=self.form, model=self.model,
            obj=self.obj, view=self.view, form_set=self.form_set)

    def _get_obj(self, request):
        return self.model.objects.get_or_create(user=request.user)[0]


class AjaxViewMixin(object):
    def get_user_or_404(self, model):
        data = get_data(self.request)
        return get_object_or_404(model, user__id=data.get('user_pk'))
