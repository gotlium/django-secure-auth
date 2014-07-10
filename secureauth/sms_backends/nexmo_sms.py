# -*- coding: utf-8 -*-

from urllib import urlopen, urlencode
from json import loads


class Nexmo(object):
    def __init__(self, *auth):
        self.params = {
            'api_key': auth[0],
            'api_secret': auth[1],
        }

    def send_sms(self, msg_from, msg_to, msg_body):
        self.params.update({
            'to': msg_to.replace('+', ''), 'from': msg_from, 'type': 'unicode',
            'text': msg_body.encode('utf-8', 'ignore')
        })

        url = urlopen(
            'https://rest.nexmo.com/sms/json?%s' % urlencode(self.params))
        messages = loads(url.read()).get('messages')
        if messages and len(messages):
            return messages[0].get('status') == '0'
