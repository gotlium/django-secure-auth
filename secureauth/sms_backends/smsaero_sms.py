# -*- coding: utf-8 -*-

from urllib import urlopen, urlencode


class SmsAero(object):
    def __init__(self, *auth):
        self.params = {
            'user': auth[0],
            'password': auth[1],
        }

    def send_sms(self, msg_from, msg_to, msg_body):
        self.params.update({
            'to': msg_to.replace('+', ''), 'from': msg_from,
            'text': msg_body.encode('utf-8')
        })

        url = urlopen(
            'http://gate.smsaero.ru/send/?%s' % urlencode(self.params))
        return 'accepted' in url.read()
