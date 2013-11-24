# -*- coding: utf-8 -*-

from twilio.rest import TwilioRestClient


class Twilio(object):
    def __init__(self, *auth):
        self.client = TwilioRestClient(*auth)

    def send_sms(self, msg_from, msg_to, msg_body):
        self.client.sms.messages.create(
            to=msg_to, from_=msg_from, body=msg_body
        )
        return True
