from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns


admin.autodiscover()


urlpatterns = patterns('',
    url(r'^$', 'movies.views.calendar'),
    url(r'^checkins/(?P<screening_id>\d+)/$', 'movies.views.checkin'),
    url(r'^checkins/$', 'movies.views.get_checkins'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^facebook/', include('django_facebook.urls')),
    url(r'^accounts/', include('django_facebook.auth_urls')),
)

urlpatterns += staticfiles_urlpatterns()
