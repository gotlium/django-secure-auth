# -*- coding: utf-8 -*-

from django_tables2 import tables

from secureauth.defaults import ACTIVITY_PER_PAGE
from secureauth.models import UserAuthActivity


class UserAuthActivityTable(tables.Table):
    class Meta:
        model = UserAuthActivity
        fields = ('ip', 'geo', 'date', 'agent')
        order_by = ('id',)
        per_page = ACTIVITY_PER_PAGE
