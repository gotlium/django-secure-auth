from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls import patterns, include, url
from django.contrib import admin
from secureauth.adminsite import site

admin.site = site
admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^$', 'secureauth.views.login'),
    url(r'^accounts/', include('secureauth.urls')),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout'),
    url(r'^accounts/', include('secureauth.registration.urls')),
    url(r'^accounts/', include('registration.backends.default.urls')),
    url(r'^rosetta/', include('rosetta.urls')),
)

urlpatterns += staticfiles_urlpatterns()
