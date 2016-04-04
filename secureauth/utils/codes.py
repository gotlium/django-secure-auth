# -*- coding: utf-8 -*-

import string
import random
import hashlib


class RandomPassword(object):
    def __init__(self):
        self.max_value = None

    def _approved(self, password):
        group = self._select(password[0])
        for character in password[1:]:
            trial = self._select(character)
            if trial is group:
                return False
            group = trial
        return True

    @staticmethod
    def _select(character):
        for group in (string.ascii_uppercase,
                      string.ascii_lowercase,
                      string.digits):
            if character in group:
                return group
        raise ValueError('Character was not found in any group!')

    def _ascii(self):
        total = string.ascii_letters + string.digits
        password = ''.join(random.sample(total, self.max_value))
        while not self._approved(password):
            password = ''.join(random.sample(total, self.max_value))
        return password

    def _digits(self):
        password = random.sample(string.digits, self.max_value)
        random.shuffle(password)
        return ''.join(password)

    def get(self, max_value=15, ascii=False):
        self.max_value = max_value
        if ascii is True:
            return self._ascii()
        else:
            return self._digits()


def md5(input_string):
    return hashlib.md5(input_string).hexdigest()
