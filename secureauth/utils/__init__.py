# -*- coding: utf-8 -*-

import struct
import socket

from django.core.mail import send_mail as dj_send_mail
from django.utils.translation import ugettext as _
from django.template import Context, loader
from django.contrib.gis.geoip import GeoIP
from django.conf import settings
from django.contrib.auth import authenticate
from django.http import Http404

from secureauth import defaults
from secureauth.defaults import SMS_AGE
from secureauth.utils.sign import Sign

from ipware.ip import get_real_ip
import phonenumbers


__all__ = ["send_sms", "send_mail", "get_ip", "get_geo",
           "inet_aton", "is_phone", "get_data"]


def _send_sms(*args, **kwargs):
    module_name = '%s_sms' % defaults.SMS_BACKEND.lower()
    backend = __import__(
        'secureauth.sms_backends.%s' % module_name,
        fromlist="sms_backends"
    )
    backend = getattr(backend, defaults.SMS_BACKEND)
    return backend(
        *defaults.SMS_BACKEND_AUTH).send_sms(*args, **kwargs)


def _send_mail(msg_to, msg_subjects, msg_body,
               msg_from=settings.DEFAULT_FROM_EMAIL):
    if isinstance(msg_to, str) or isinstance(msg_to, unicode):
        msg_to = [msg_to]
    dj_send_mail(msg_subjects, msg_body, msg_from, msg_to)


if defaults.USE_CELERY is True:
    from celery.task import Task

    class _SMSSendTask(Task):
        def run(self, *args, **kwargs):
            _send_sms(*args, **kwargs)

    class _MailSendTask(Task):
        def run(self, *args, **kwargs):
            _send_mail(*args, **kwargs)
else:
    class _SMSSendTask(object):
        @staticmethod
        def delay(*args, **kwargs):
            _send_sms(*args, **kwargs)

    class _MailSendTask(object):
        @staticmethod
        def delay(*args, **kwargs):
            _send_mail(*args, **kwargs)


def send_sms(*args, **kwargs):
    _SMSSendTask.delay(*args, **kwargs)


def send_mail(*args, **kwargs):
    _MailSendTask.delay(*args, **kwargs)


def get_ip(request):
    ip_address = get_real_ip(request)
    if ip_address is not None:
        return ip_address.strip()
    return request.META['REMOTE_ADDR'].strip()


def inet_aton(ip_address):
    return struct.unpack('!L', socket.inet_aton(ip_address))[0]


def get_geo(ip, unknown=_('Unknown')):
    geo_ip = GeoIP()
    info = geo_ip.city(ip) or dict()
    return "%s:%s" % (
        info.get('country_name') or unknown,
        info.get('city') or unknown,
    )


def is_phone(phone):
    try:
        return phonenumbers.is_valid_number(phonenumbers.parse(phone, None))
    except phonenumbers.NumberParseException:
        return False


def get_formatted_phone(phone):
    return phonenumbers.format_number(
        phonenumbers.parse(phone), phonenumbers.PhoneNumberFormat.E164
    )


def render_template(template, context=None):
    template = loader.get_template(template)
    return template.render(Context(context or {}))


def get_data(request):
    data = Sign().unsign(request.GET.get('data'), age=SMS_AGE * 2)
    if data is not None and 'credentials' in data:
        if 'captcha' in data['credentials']:
            data['credentials'].pop('captcha')
        user = authenticate(**data['credentials'])
        if user is not None and user.is_active:
            if get_ip(request) == data.get('ip'):
                return data
    raise Http404('Data is not valid!')
