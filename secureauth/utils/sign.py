# -*- coding: utf-8 -*-

from django.core.signing import BadSignature, SignatureExpired
from django.core import signing


class Sign(object):
    def __init__(self, salt=None):
        self.signer = signing.TimestampSigner(salt=salt)

    def sign(self, data):
        return self.signer.sign(signing.dumps({"data": data}, compress=True))

    def unsign(self, signed, age=None):
        try:
            value = self.signer.unsign(signed, max_age=age)
            return signing.loads(value).get('data')
        except (BadSignature, SignatureExpired):
            pass
