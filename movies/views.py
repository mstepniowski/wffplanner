# -*- coding: utf-8 -*-
import json
import logging
from facepy import GraphAPI, exceptions

from django.views.generic.simple import direct_to_template
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import F

from movies.models import Calendar, Checkin, Screening


logger = logging.getLogger('django')


@ensure_csrf_cookie
def calendar(request):
    c = Calendar()
    return direct_to_template(request,
                              template='movies/calendar.html',
                              extra_context={'calendar': c})


@login_required
@require_POST
@never_cache
def checkin(request, screening_id):
    social_auth = request.user.get_profile()
    graph = GraphAPI(social_auth.access_token)

    try:
        checkin = Checkin.objects.get(user=request.user,
                                      screening_id=int(screening_id))
        Screening.objects.filter(id=int(screening_id)).update(attendees_count=F('attendees_count') - 1)
        checkin.delete()
    except Checkin.DoesNotExist:
        Checkin.objects.create(user=request.user,
                               screening_id=int(screening_id),
                               facebook_id=social_auth.facebook_id)
        Screening.objects.filter(id=int(screening_id)).update(
            attendees_count=F('attendees_count') + 1)
        try:
            graph.post('me/wffplanner:planning_to_watch',
                       movie='http://wffplanner.stepniowski.com/')
        except exceptions.FacebookError, e:
            logging.exception('Error when posting to OpenGraph: %s' % e.message)
        except:
            logging.exception('Error when posting to OpenGraph')
            
    
    return HttpResponse('OK')


@never_cache
def get_checkins(request):
    if not request.user.is_authenticated():
        return HttpResponse(json.dumps({'my_checkins': [], 'friend_checkins': []}),
                            mimetype='application/json')

    social_auth = request.user.get_profile()
    graph = GraphAPI(social_auth.access_token)
    friends = sum([d['data'] for d in graph.get('me/friends', page=True)], [])
    friend_ids = [friend['id'] for friend in friends]

    friend_checkins = [{'facebook_id': ch.facebook_id, 'id': ch.screening_id}
                       for ch in Checkin.objects.filter(facebook_id__in=friend_ids)]
    
    return HttpResponse(json.dumps({
        'my_checkins': [{'facebook_id': ch.facebook_id, 'id': ch.screening_id}
                         for ch in Checkin.objects.filter(user=request.user)],
        'friend_checkins': friend_checkins
    }), mimetype='application/json')


WEEKDAYS = [u"poniedziałek", "wtorek", u"środa", "czwartek", u"piątek", "sobota", "niedziela"]


@login_required
@never_cache
def screening_list(request):
    if not request.user.is_authenticated():
        return HttpResponse('')

    result = []
    screenings = Screening.objects.filter(checkin__user=request.user).select_related('movie')
    for screening in sorted(screenings, key=lambda screening: (screening.date, screening.room)):
        result.append(u"%s, %s (%s) — %s" % (WEEKDAYS[screening.date.weekday()],
                                            screening.date.strftime('%d.X %H:%M'),
                                            screening.room,
                                            screening.movie.title))
    return HttpResponse('<br>\n<center></center>'.join(result))
            
    
