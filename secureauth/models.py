# -*- coding: utf-8 -*-

import datetime
import random
import json

from django.utils.translation import ugettext as _
from django.core.exceptions import ValidationError
from django.contrib.sites.models import Site
from django.utils.timezone import utc
from django.contrib import messages
from django.db import models
from django.conf import settings

from httpagentparser import detect

from secureauth.utils.token import random_seed, check_seed, get_google_url
from secureauth.utils.codes import RandomPassword
from secureauth.utils import send_sms, send_mail
from secureauth.utils import get_ip, get_geo
from secureauth.utils.sign import Sign
from secureauth.defaults import (
    SMS_MESSAGE, SMS_CODE_LEN, SMS_AGE, SMS_FROM,
    CODE_RANGES, SMS_NOTIFICATION_MESSAGE, SMS_NOTIFICATION_SUBJECT)


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
        self.last_verified = datetime.datetime.utcnow().replace(tzinfo=utc)
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
            data[i] = rand.get(max_value=8)
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
        return dict(
            codes=json.loads(Sign().unsign(self.code)),
            number=self.get_code_number()
        )


class UserAuthToken(UserAuthAbstract):
    def get_google_url(self):
        return get_google_url(
            Sign().unsign(self.code),
            "%s@%s" % (
                self.user.get_full_name(), Site.objects.get_current().domain)
        )

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
        if not self.pk and not self.phone.startswith('+'):
            raise ValidationError(
                _('Phone does not contain spaces and must be starts with a +'))

    def save(self, *args, **kwargs):
        if self.phone.startswith('+'):
            self.phone = Sign().sign(self.phone)
        super(UserAuthPhone, self).save(*args, **kwargs)

    def send_sms(self):
        code = str(RandomPassword().get(SMS_CODE_LEN)).lower()
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
    ip = models.CharField(max_length=40)
    geo = models.CharField(_('GEO'), max_length=255, null=True, blank=True)
    date = models.DateTimeField(_('Date'), auto_now_add=True)
    agent = models.CharField(
        _('Browser'), max_length=255, null=True, blank=True)

    class Meta:
        ordering = ('-id',)

    @classmethod
    def log_auth(cls, request):
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
            agent=user_agent
        )

    @classmethod
    def check_location(cls, request):
        obj = cls.objects.filter(user=request.user).order_by('-id')[:1]
        if obj.exists() and get_geo(get_ip(request)) != obj[0].geo:
            show_msg = """%s<br/>GEO: %s<br/>IP: %s<br/>PC: %s<br/>%s""" % (
                unicode(_('Your location has changed. Former location:')),
                obj[0].geo, obj[0].ip, obj[0].agent, unicode(
                    _('If it was not you, then change authorization data.')))
            messages.warning(request, show_msg)
