# -*- coding: utf-8 -*-
from django import template

from secureauth.defaults import METHODS_ENABLED, SMS_FORCE

register = template.Library()


@register.tag
def enabled(parser, token):
    nodelist = parser.parse(('endenabled',))
    parser.delete_first_token()
    auth_type = token.contents.split()[-1]
    return EnabledNode(nodelist, auth_type)


class EnabledNode(template.Node):
    def __init__(self, nodelist, auth_type):
        self.nodelist = nodelist
        self.auth_type = auth_type

    def render(self, context):
        if self.auth_type in METHODS_ENABLED or (
                SMS_FORCE and self.auth_type == 'phone'):
            return self.nodelist.render(context)
        return ""
