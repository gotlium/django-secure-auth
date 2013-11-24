# -*- coding: utf-8 -*-

from django_filters import FilterSet, DateRangeFilter, ChoiceFilter
from django.utils.translation import ugettext_lazy as _
from models import UserAuthActivity


class UserAuthActivityFilter(FilterSet):
    date = DateRangeFilter(label=_('Date'))
    ip = ChoiceFilter(label=_('IP'))

    class Meta:
        model = UserAuthActivity
        fields = ['date', 'ip']

    def __init__(self, *args, **kwargs):
        super(UserAuthActivityFilter, self).__init__(*args, **kwargs)
        self.filters['ip'].extra.update({
            'choices': tuple(
                set(self.queryset.values_list('ip', 'ip'))
            )
        })
