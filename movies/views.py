import json
import logging
from facepy import GraphAPI

from django.views.generic.simple import direct_to_template
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from movies.models import Calendar, Checkin


logger = logging.getLogger('django')


@ensure_csrf_cookie
def calendar(request):
    c = Calendar()
    return direct_to_template(request,
                              template='movies/calendar.html',
                              extra_context={'calendar': c})


@login_required
@require_POST
def checkin(request, screening_id):
    social_auth = request.user.social_auth.get(provider='facebook')
    graph = GraphAPI(social_auth.tokens['access_token'])

    try:
        checkin = Checkin.objects.get(user=request.user,
                                      screening_id=int(screening_id))
        checkin.delete()
    except Checkin.DoesNotExist:
        Checkin.objects.create(user=request.user,
                               screening_id=int(screening_id),
                               facebook_id=social_auth.extra_data['id'])
        try:
            graph.post('me/wffplanner:planning_to_watch',
                       movie='http://wffplanner.stepniowski.com/')
        except:
            logging.exception('Error when posting to OpenGraph')
    
    return HttpResponse('OK')


@login_required
def get_checkins(request):
    social_auth = request.user.social_auth.get(provider='facebook')
    graph = GraphAPI(social_auth.tokens['access_token'])
    friends = sum([d['data'] for d in graph.get('me/friends', page=True)], [])
    friend_ids = [friend['id'] for friend in friends]

    friend_checkins = [{'facebook_id': ch.facebook_id, 'id': ch.screening_id} for
                       ch in Checkin.objects.filter(facebook_id__in=friend_ids)]
    
    return HttpResponse(json.dumps({
        'my_checkins': [checkin.screening_id for checkin 
                        in Checkin.objects.filter(user=request.user)],
        'friend_checkins': friend_checkins
    }), mimetype='application/json')
