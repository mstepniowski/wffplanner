from django.contrib import admin
from django import forms

from movies.models import Movie, Screening, Checkin, Festival
from movies.fields import JSONFormField


class MovieForm(forms.ModelForm):
    info = JSONFormField()
    class Meta:
        model = Movie


class MovieAdmin(admin.ModelAdmin):
    list_display = ['title', 'get_link']
    list_filter = ['festival']
    form = MovieForm
    
    def get_link(self, obj):
        return '<a href="%(url)s">%(url)s</a>' % {'url': obj.url}
    get_link.short_descritpion = 'Link'
    get_link.allow_tags = True

admin.site.register(Movie, MovieAdmin)


class FestivalAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_link']

    def get_link(self, obj):
        return '<a href="%(url)s">%(url)s</a>' % {'url': obj.url}
    get_link.short_descritpion = 'Link'
    get_link.allow_tags = True

admin.site.register(Festival, FestivalAdmin)

    
class ScreeningAdmin(admin.ModelAdmin):
    list_display = ['movie', 'room', 'date']

admin.site.register(Screening, ScreeningAdmin)


class CheckinAdmin(admin.ModelAdmin):
    list_display = ['user', 'screening']

admin.site.register(Checkin, CheckinAdmin)
