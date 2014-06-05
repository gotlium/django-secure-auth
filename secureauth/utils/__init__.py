# -*- coding: utf-8 -*-

import struct
import socket

from django.core.mail import send_mail as dj_send_mail
from django.contrib.gis.geoip import GeoIP
from django.conf import settings

from secureauth.defaults import USE_CELERY
from secureauth import defaults

from ipware.ip import get_real_ip
import phonenumbers


__all__ = ["send_sms", "send_mail", "get_ip", "get_geo",
           "inet_aton", "is_phone"]


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


if USE_CELERY is True:
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
    ip = get_real_ip(request)
    if ip is not None:
        return ip
    else:
        ip = request.META['REMOTE_ADDR']
        if 'HTTP_X_FORWARDED_FOR' in request.META:
            ip = request.META['HTTP_X_FORWARDED_FOR'].split(',')[-1]
        return ip.strip()


def inet_aton(ip):
    return struct.unpack('!L', socket.inet_aton(ip))[0]


def get_geo(ip):
    g = GeoIP()
    info = g.city(ip)
    if info is None:
        info = dict()
    return "%s:%s" % (
        info.get('country_name', 'Unknown') or 'Unknown',
        info.get('city', 'Unknown') or 'Unknown',
    )


def is_phone(phone):
    z = phonenumbers.parse(phone, None)
    return phonenumbers.is_valid_number(z)
