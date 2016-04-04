# -*- encoding: utf-8 -*-

from re import compile as re_compile
from urllib import quote
from time import time

from django.http import HttpResponseBadRequest
from django.contrib.auth import logout
from django.shortcuts import render

from aes import AESModeOfOperation

from secureauth.defaults import (
    TEST_COOKIE_ENABLED_URLS, TEST_COOKIE_ENABLED,
    TEST_COOKIE_REFRESH_ENCRYPT_COOKIE_IV,
    TEST_COOKIE_REFRESH_ENCRYPT_COOKIE_KEY,
)
from secureauth.utils import render_template, get_ip
from secureauth.utils.codes import RandomPassword
from secureauth.defaults import SESSION_MAX
from secureauth.models import UserAuthAttempt


ENABLED_URLS = [re_compile(expr) for expr in TEST_COOKIE_ENABLED_URLS]


class SecureAuthFixedSessionIPMiddleware(object):
    def process_request(self, request):
        if request.session.get('ip'):
            if request.session.get('ip') != get_ip(request):
                del request.session['ip']
                logout(request)


class SecureAuthSessionExpireMiddleware(object):
    def process_request(self, request):
        if request.session.get('last_activity'):
            if (time() - request.session.get('last_activity')) > SESSION_MAX:
                if hasattr(request, 'user'):
                    if request.user.is_authenticated():
                        logout(request)

        request.session['last_activity'] = time()


class SecureAuthTestCookieMiddleware(object):
    def process_request(self, request):
        if self._is_enabled(request):
            if not request.session.get('test_cookie_secret'):
                request.session['test_cookie_secret'] = str(
                    RandomPassword().get(ascii=True))
                request.session.save()

            if not request.COOKIES.get('satctoken'):
                UserAuthAttempt.clean()
                UserAuthAttempt.store(request)

    def process_response(self, request, response):
        if not self._is_enabled(request):
            return response

        if UserAuthAttempt.is_banned(request):
            return HttpResponseBadRequest()

        if not request.COOKIES.get('satctoken'):
            iv = TEST_COOKIE_REFRESH_ENCRYPT_COOKIE_IV
            key = TEST_COOKIE_REFRESH_ENCRYPT_COOKIE_KEY

            moo = AESModeOfOperation()
            encrypted = moo.encrypt(
                request.session['test_cookie_secret'], 2,
                map(ord, key), moo.aes.keySize["SIZE_128"], map(ord, iv)
            )
            sec_uni = u''.join(map(unichr, encrypted[2]))

            return render(
                request, 'secureauth/test_cookie.html', {
                    'test_cookie_enc_key': key,
                    'test_cookie_enc_iv': iv,
                    'test_cookie_enc_set': quote(sec_uni.encode("utf-8")),
                    'test_cookie_next_url': request.get_full_path(),
                })
        elif response.status_code == 200:
            from_cookie = request.COOKIES.get('satctoken').decode('hex')
            from_session = request.session.get('test_cookie_secret')
            if from_session is None:
                self._clean(request, response)
            elif from_cookie != from_session:
                response.content = render_template(
                    'secureauth/session_expired.html')
                self._clean(request, response)
                logout(request)
                return response
        return response

    @staticmethod
    def _is_enabled(request):
        if not TEST_COOKIE_ENABLED:
            return False
        path = request.path_info.lstrip('/')
        return any(m.match(path) for m in ENABLED_URLS)

    @staticmethod
    def _clean(request, response):
        if request.session.get('test_cookie_secret'):
            del request.session['test_cookie_secret']
        if request.COOKIES.get('satctoken'):
            response.delete_cookie('satctoken')
