# coding=utf-8;

from functools import wraps

from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.http import HttpResponseBadRequest


def ajax_required(func):
    @wraps(func)
    def wrap(request, *args, **kwargs):
        if not request.is_ajax():
            return HttpResponseBadRequest()
        return func(request, *args, **kwargs)
    return wrap


def login_decorator(func):
    return csrf_protect(never_cache(sensitive_post_parameters()(func)))


class StaffDecoratorMixin(object):
    @method_decorator(login_required)
    @method_decorator(staff_member_required)
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        return super(StaffDecoratorMixin, self).dispatch(*args, **kwargs)


class AuthDecoratorMixin(object):
    @method_decorator(login_required)
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        return super(AuthDecoratorMixin, self).dispatch(*args, **kwargs)


class AjaxDecoratorMixin(object):
    @method_decorator(ajax_required)
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        return super(AjaxDecoratorMixin, self).dispatch(*args, **kwargs)
