from django.shortcuts import HttpResponse
from .admin import *


def csrf_failure(request, *args, **kwargs):
    return HttpResponse(
        'Page is expired or something wrong. Go to main page and try again.')
