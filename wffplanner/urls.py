from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns


admin.autodiscover()


urlpatterns = patterns('',
    url(r'^$', 'wffplanner.views.index'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^social/', include('social_auth.urls')),
)

urlpatterns += staticfiles_urlpatterns()
