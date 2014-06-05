# -*- coding: utf-8 -*-

import collections
import datetime
import random
import json

from django.utils.translation import ugettext as _
from django.core.exceptions import ValidationError
from django.forms.models import model_to_dict
from django.contrib.sites.models import Site
from django.utils.timezone import now
from django.contrib import messages
from django.db import models
from django.conf import settings

from httpagentparser import detect

from secureauth.utils.token import random_seed, check_seed, get_google_url
from secureauth.utils import get_ip, get_geo, inet_aton
from secureauth.utils.codes import RandomPassword
from secureauth.utils import send_sms, send_mail
from secureauth.utils.sign import Sign
from secureauth.utils import is_phone
from secureauth.defaults import (
    SMS_MESSAGE, SMS_CODE_LEN, SMS_ASCII, SMS_AGE, SMS_FROM,
    CODE_RANGES, CODE_LEN, SMS_NOTIFICATION_MESSAGE, SMS_NOTIFICATION_SUBJECT,
    LOGIN_ATTEMPT, BAN_TIME, CHECK_ATTEMPT, CODES_SUBJECT, TOTP_NAME)


AUTH_TYPES = (
    ('', '---'),
    ('code', _('by code')),
    ('token', _('by token')),
    ('phone', _('by sms')),
    ('question', _('by question')),
)


class UserAuthAbstract(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, editable=False, verbose_name=_('User'))
    code = models.TextField()
    enabled = models.BooleanField(_('Enabled'), default=False)
    created = models.DateTimeField(
        _('Created'), auto_now_add=True, editable=False)
    updated = models.DateTimeField(
        _('Updated'), auto_now=True, editable=False)
    last_verified = models.DateTimeField(
        _('Last verified'), blank=True, null=True, editable=False)

    def update_last_verified(self):
        self.last_verified = now()
        self.save(update_fields=['last_verified'])

    def check_auth_code(self, auth_code, force_check=False):
        if (self.code and self.enabled) or force_check:
            if self._code_is_valid(auth_code):
                return True

    def make(self):
        return True

    def get_data(self):
        return ""

    class Meta:
        abstract = True


class UserAuthCode(UserAuthAbstract):
    number = models.TextField(_('Number'), blank=True, null=True)

    def generate_codes(self):
        data = {}
        rand = RandomPassword()
        for i in range(1, CODE_RANGES + 1):
            data[i] = rand.get(max_value=CODE_LEN)
        self.code = Sign().sign(json.dumps(data))
        return self.save()

    def _code_is_valid(self, code):
        data = json.loads(Sign().unsign(self.code))
        number = str(Sign().unsign(self.number, SMS_AGE))
        return str(code) == str(data.get(number))

    def get_code_number(self):
        number = random.choice(range(1, CODE_RANGES + 1))
        self.number = Sign().sign(number)
        self.save(update_fields=['number'])
        return number

    def make(self):
        self.generate_codes()

    def get_data(self):
        codes = json.loads(Sign().unsign(self.code))
        data = collections.OrderedDict(
            sorted(codes.items(), key=lambda t: int(t[0])))
        return dict(
            codes=data,
            number=self.get_code_number()
        )

    @classmethod
    def send_codes(cls, request):
        settings_list = cls.objects.filter(user=request.user)

        if settings_list.exists():
            created_seconds = (now() - settings_list[0].created).seconds
            if created_seconds > 300:
                return

            codes = json.loads(Sign().unsign(settings_list[0].code))
            codes_list = collections.OrderedDict(
                sorted(codes.items(), key=lambda t: int(t[0])))
            message = ''
            for (k, v) in codes_list.items():
                message += '%s. %s\n' % (k, v)
            send_mail(
                [request.user.email], CODES_SUBJECT, message
            )
            return True


class UserAuthToken(UserAuthAbstract):
    def get_google_url(self):
        data = model_to_dict(Site.objects.get_current())
        data.update(model_to_dict(self.user))
        return get_google_url(Sign().unsign(self.code), TOTP_NAME % data)

    def _code_is_valid(self, code):
        return check_seed(Sign().unsign(self.code), int(code))

    def make(self):
        if not self.code:
            self.code = Sign().sign(random_seed())
            self.save()

    def get_data(self):
        return self.get_google_url()


class UserAuthPhone(UserAuthAbstract):
    phone = models.CharField(_('Phone'), max_length=255, unique=True)

    def clean(self):
        if not is_phone(self.phone) or not self.phone.startswith('+'):
            raise ValidationError(
                _('Phone does not contain spaces and must be starts with a +'))

    def save(self, *args, **kwargs):
        if str(self.phone).startswith('+'):
            self.phone = Sign().sign(self.phone)
        super(UserAuthPhone, self).save(*args, **kwargs)

    def send_sms(self):
        code = str(RandomPassword().get(SMS_CODE_LEN, SMS_ASCII)).lower()
        send_sms(SMS_FROM, Sign().unsign(self.phone), SMS_MESSAGE % code)
        self.code = Sign().sign(code)
        self.save()

    def _code_is_valid(self, code):
        return str(Sign().unsign(self.code, SMS_AGE)) == str(code)

    def make(self):
        self.send_sms()


class UserAuthQuestion(UserAuthAbstract):
    question = models.TextField(_('Question'))

    def set_data(self, question, answer):
        self.code = Sign().sign(answer)
        self.question = Sign().sign(question)
        self.save()
        return self

    def get_question(self):
        return Sign().unsign(self.question)

    def _code_is_valid(self, code):
        return Sign().unsign(self.code) == code

    def get_data(self):
        return self.get_question()


class UserAuthNotification(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, verbose_name=_('User'))
    enabled = models.BooleanField(_('Enabled'), default=False)

    @classmethod
    def notify(cls, request, message=None, force=False):
        obj = cls.objects.filter(user=request.user)
        if (obj.exists() and obj[0].enabled) or force:
            obj = UserAuthPhone.objects.filter(user=request.user)
            message = message if message else SMS_NOTIFICATION_MESSAGE
            if obj.exists():
                send_sms(SMS_FROM, Sign().unsign(obj[0].phone), message)
            elif request.user.email:
                send_mail(
                    [request.user.email], SMS_NOTIFICATION_SUBJECT, message)


class UserAuthActivity(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, editable=False, verbose_name=_('User'))
    ip = models.CharField(max_length=40, db_index=True)
    geo = models.CharField(_('GEO'), max_length=255, null=True, blank=True)
    date = models.DateTimeField(_('Date'), auto_now_add=True)
    agent = models.CharField(
        _('Browser'), max_length=255, null=True, blank=True)
    confirm_method = models.CharField(
        _('Confirm method'), max_length=10, choices=AUTH_TYPES,
        null=True, blank=True)

    class Meta:
        ordering = ('-id',)

    @classmethod
    def log_auth(cls, request, confirm_method=''):
        ip = get_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT')
        if user_agent is not None:
            parser = detect(user_agent)
            browser = parser.get('browser', {})
            user_agent = "%s, %s %s" % (
                parser.get('platform', {}).get('name', ""),
                browser.get('name', ""), browser.get('version', ""))
        cls.objects.create(
            user=request.user, ip=get_ip(request), geo=get_geo(ip),
            agent=user_agent, confirm_method=confirm_method
        )

    @classmethod
    def check_location(cls, request):
        obj = cls.objects.filter(user_id=request.user.pk).order_by('-id')[:1]
        if obj.exists() and get_geo(get_ip(request)) != obj[0].geo:
            show_msg = """%s<br/>GEO: %s<br/>IP: %s<br/>PC: %s<br/>%s""" % (
                unicode(_('Your location has changed. Former location:')),
                obj[0].geo, obj[0].ip, obj[0].agent, unicode(
                    _('If it was not you, then change authorization data.')))
            messages.warning(request, show_msg)
            UserAuthNotification.notify(
                request,
                _('Your location has changed to %s' % get_geo(get_ip(request)))
            )


class UserAuthAttempt(models.Model):
    ip = models.BigIntegerField(db_index=True)
    attempt = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now=True, auto_now_add=True)

    @classmethod
    def get_obj(cls, request):
        return cls.objects.get_or_create(ip=inet_aton(get_ip(request)))[0]

    @classmethod
    def store(cls, request):
        obj = cls.get_obj(request)
        obj.attempt = models.F('attempt') + 1
        obj.save(update_fields=['attempt'])

    @classmethod
    def remove(cls, request):
        if CHECK_ATTEMPT is True:
            obj = cls.get_obj(request)
            obj.delete()

    @classmethod
    def is_banned(cls, request):
        obj = cls.get_obj(request)
        if obj.attempt > LOGIN_ATTEMPT:
            if (now() - obj.created).seconds < BAN_TIME:
                return True

    @classmethod
    def clean(cls):
        old = now() - datetime.timedelta(seconds=BAN_TIME)
        cls.objects.filter(created__lt=old).delete()


class UserAuthLogging(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, verbose_name=_('User'))
    enabled = models.BooleanField(_('Enabled'), default=False)

    @classmethod
    def is_enabled(cls, request):
        return cls.objects.filter(user=request.user, enabled=1).exists()
