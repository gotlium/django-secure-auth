# -*- coding: utf-8 -*-

from django_filters import FilterSet, DateRangeFilter, ChoiceFilter
from django.utils.translation import ugettext_lazy as _
from secureauth.models import UserAuthActivity


class UserAuthActivityFilter(FilterSet):
    date = DateRangeFilter(label=_('Date'))
    ip = ChoiceFilter(label=_('IP'), required=False)

    class Meta:
        model = UserAuthActivity
        fields = ['date', 'ip']

    def __init__(self, *args, **kwargs):
        super(UserAuthActivityFilter, self).__init__(*args, **kwargs)
        ip_list = self.queryset.distinct().values_list('ip', flat=1).order_by()
        self.filters['ip'].extra.update({
            'choices': [('', '----')] + [(ip, ip) for ip in ip_list]
        })
