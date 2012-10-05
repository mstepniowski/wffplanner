var screenings = '';

// Django CSRF magic
function getCookie(name) {
    var i;
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
var csrftoken = getCookie('csrftoken');

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
function sameOrigin(url) {
    // test that a given url is a same-origin URL
    // url could be relative or scheme relative or absolute
    var host = document.location.host; // host + port
    var protocol = document.location.protocol;
    var sr_origin = '//' + host;
    var origin = protocol + sr_origin;
    // Allow absolute or scheme relative URLs to same origin
    return (url === origin || url.slice(0, origin.length + 1) === origin + '/') ||
        (url === sr_origin || url.slice(0, sr_origin.length + 1) === sr_origin + '/') ||
        // or any other URL that isn't scheme relative or absolute i.e relative.
        !(/^(\/\/|http:|https:).*/.test(url));
}
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
            // Send the token to same-origin, relative URLs only.
            // Send the token only if the method warrants CSRF protection
            // Using the CSRFToken value acquired earlier
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});


$(function() {
    $.getJSON('checkins/', function (data) {
        $.each(data.my_checkins, function () {
            $('#' + this.id).addClass('active');
            $('#' + this.id + ' .attendees').append('<img class="avatar me" src="//graph.facebook.com/' + this.facebook_id + '/picture" />');
            var attendees_count = parseInt($('#' + this.id + ' .count').text(), 10);
            attendees_count--;
            if (attendees_count === 0) {
                $('#' + this.id + ' .count').remove();
            } else {
                $('#' + this.id + ' .count').text(attendees_count);
            }
        });
        $.each(data.friend_checkins, function () {
            $('#' + this.id + ' .attendees').append('<img class="avatar" src="//graph.facebook.com/' + this.facebook_id + '/picture" />');
            var attendees_count = parseInt($('#' + this.id + ' .count').text(), 10);
            attendees_count--;
            if (attendees_count === 0) {
                $('#' + this.id + ' .count').remove();
            } else {
                $('#' + this.id + ' .count').text(attendees_count);
            }
        });

        $('.count').each(function () {
            $(this).text('+' + $(this).text());
        });
    });

    $.get('/screenings/', function (text) { screenings = text; });
    
    $('.screening').click(function () {
        if ($(this).hasClass('active')) {
            $(this).removeClass('active').find('.me').remove();
        } else {
            $(this).addClass('active').find('.attendees').append('<img class="avatar me" src="//graph.facebook.com/' + MY_ID + '/picture" />');
        }
        $.post('checkins/' + $(this).attr('id') + '/');
        $.get('/screenings/', function (text) { screenings = text; });
    });

    $('#schedule').scroll(function () {
        $('#rooms').scrollTop($(this).scrollTop());
    });

    $('#facebook-share').click(function () {
        FB.ui({
            method: 'feed',
            link: 'http://wffplanner.stepniowski.com/',
            picture: 'http://wffplanner.stepniowski.com/static/wffplanner.png',
            name: 'Mój harmonogram na Warsaw Film Festival',
            description: screenings
        }, function () {
            _gaq.push(['_trackSocial', 'facebook', 'send']);
        });
    });
});


