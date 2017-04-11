# coding=utf-8;

from django.conf.urls import url, include

import secureauth.views as v

urlpatterns = [
    url(r'^$', 'login'),
    url(r'^login/$', 'login', name='auth_login'),
    url('^confirmation/$', 'login_confirmation', name='auth_confirmation'),

    url('^code_get_random/$', v.CodeGetRandomView.as_view(),
        name='code_get_random'),
    url('^phone_send_sms/$', v.PhoneSendSmsView.as_view(),
        name='phone_send_sms'),
    url('^get_question/$', v.GetQuestionView.as_view(), name='get_question'),

    url('^settings/$', v.AuthSettingsView.as_view(), name='auth_settings'),
    url('^totp_settings/$', v.TotpSettingsView.as_view(),
        name='totp_settings'),
    url('^phone_settings/$', v.PhoneSettingsView.as_view(),
        name='phone_settings'),
    url('^codes_settings/$', v.CodesSettingsView.as_view(),
        name='codes_settings'),
    url('^question_settings/$', v.QuestionSettingsView.as_view(),
        name='question_settings'),
    url('^auth_activity/$', v.AuthActivityView.as_view(),
        name='auth_activity'),
    url('^notify_settings/$', v.NotifySettingsView.as_view(),
        name='notify_settings'),
    url('^logging_settings/$', v.LoggingSettingsView.as_view(),
        name='logging_settings'),
    url('^ip_settings/$', v.IpSettingsView.as_view(), name='ip_settings'),
    url('^send_codes/$', v.SendCodesView.as_view(), name='send_codes'),
    url('^disable_methods/(?P<pk>\d+)/$', v.DisableMethodsView.as_view(),
        name='disable_methods'),
    url('^unban_ip/$', v.UnbanIpView.as_view(), name='unban_ip'),
    url(r'^captcha/', include('captcha.urls')),
]
