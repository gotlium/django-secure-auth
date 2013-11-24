from urllib import urlencode
from pyotp import TOTP, random_base32
from base64 import b32encode


def random_seed(size=30):
    return b32encode(random_base32(size))


def check_seed(seed, code):
    return TOTP(seed).verify(int(code))


def get_google_url(seed, hostname):
    return "https://chart.googleapis.com/chart?" + urlencode({
        "chs": "200x200",
        "chld": "M|0",
        "cht": "qr",
        "chl": TOTP(seed).provisioning_uri(hostname)
    })
