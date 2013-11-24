# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url

urlpatterns = patterns(
    'secureauth.views',
    url(r'^$', 'login'),
    url(r'^login/$', 'login', name='auth_login'),
    url('^confirmation/$', 'login_confirmation', name='auth_confirmation'),
    url('^code_get_random/$', 'code_get_random', name='code_get_random'),
    url('^phone_send_sms/$', 'phone_send_sms', name='phone_send_sms'),
    url('^get_question/$', 'get_question', name='get_question'),

    url('^settings/$', 'auth_settings', name='auth_settings'),
    url('^totp_settings/$', 'totp_settings', name='totp_settings'),
    url('^phone_settings/$', 'phone_settings', name='phone_settings'),
    url('^codes_settings/$', 'codes_settings', name='codes_settings'),
    url('^question_settings/$', 'question_settings', name='question_settings'),
    url('^auth_activity/$', 'auth_activity', name='auth_activity'),
    url('^notify_settings/$', 'notify_settings', name='notify_settings'),
)
