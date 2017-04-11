# -*- coding: utf-8 -*-

from django.conf.urls import url
from secureauth.registration.views import (
    ActivationView, ConfirmView, ActivationDoneView)
from django.views.generic.base import TemplateView


urlpatterns = [
    url(r'^activation/complete/$',
        TemplateView.as_view(
            template_name='registration/activation_complete.html'),
        name='registration_activation_complete_view'),
    url(r'^activate/(?P<activation_key>\w+)/$',
        ActivationView.as_view(),
        name='registration_activate'),
    url(r'^confirmation/(?P<activation_key>\w+)/$',
        ConfirmView.as_view(),
        name='registration_confirm'),
    url(r'^activation_done/(?P<activation_key>\w+)/$',
        ActivationDoneView.as_view(),
        name='registration_activation_done'),
    url(r'^activation_failed/$',
        TemplateView.as_view(
            template_name='secureauth/registration_activation_failed.html'),
        name='registration_activation_failed'),
]
