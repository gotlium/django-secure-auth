# -*- coding: utf-8 -*-


from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.debug import sensitive_post_parameters
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.http import HttpResponseBadRequest


def ajax_required(f):
    """
    url: https://djangosnippets.org/snippets/771/
    """

    def wrap(request, *args, **kwargs):
        if not request.is_ajax():
            return HttpResponseBadRequest()
        return f(request, *args, **kwargs)

    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap


def ajax_decorator(func):
    return ajax_required(never_cache(func))


def auth_decorator(func):
    return login_required(never_cache(func))


def staff_decorator(func):
    return login_required(staff_member_required(never_cache(func)))


def login_decorator(func):
    return csrf_protect(never_cache(sensitive_post_parameters()(func)))
