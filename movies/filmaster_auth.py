from oauth import oauth
import urllib2, cgi
import json

import logging
logger = logging.getLogger(__name__)

class FilmasterOAuthClient(object):
    """
    This class implements filmaster client for making API requests 
    authenticated with OAuth1 protocol

    Usage:
    If you don't have access token yet:
      1. create instance of this class using CONSUMER_KEY and CONSUMER_SECRET
         (obtained at http://filmaster.com/settings/application/)

         client = FilmasterOAuthClient(CONSUMER_KEY, CONSUMER_SECRET)

      2. fetch request token and temporary store it in session / db:

         request_token = client.fetch_request_token()

      3. obtain authorize_url:

         authorize_url = client.get_authorize_url(request_token, callback_url=CALLBACK_URL)

      4. redirect user's browser to authorize_url - user authenticates
         on filmaster, authorizes access of your app and is redirected back
         to CALLBACK_URL (of your app) provided earlier

      5. in CALLBACK_URL handler fetch oauth_verifier parameter from
         request GET parameters and retrieve request_token stored earlier.
         Call fetch_access_token method to retrieve access_token

         access_token = client.fetch_access_token(request_token, oauth_verifier)

      6. store access_token in db for making subsequent, authenticated API requests

    If you have access_token already, pass it to FilmasterOAuthClient constructor:

    client = FilmasterOAuthClient(CONSUMER_KEY, CONSUMER_SECRET, access_token)

    or invoke set_access_token method:

    client.set_access_token(access_token)

    make api requests using get, post, put or delete methods:

    reply = client.get('/1.1/profile/')

    """

    API_BASE_URL = "http://api.filmaster.pl"
    BASE_URL = 'http://filmaster.pl'

    REQUEST_TOKEN_URL = BASE_URL + '/oauth/request/token/'
    ACCESS_TOKEN_URL = BASE_URL + '/oauth/access/token/'

    AUTHORIZATION_URL = BASE_URL + '/oauth/authorize/'
    FB_AUTHORIZATION_URL = BASE_URL + '/oauth/authorize/fb/'

    def __init__(self, key, secret, access_token=None):
        """
        key, secret - key and secret of your app, to register app visit http://filmaster.com/settings/application/
        access_token - optional, may be set later using set_access_token method
        """
        self.consumer = oauth.OAuthConsumer(key, secret)
        self.signature = oauth.OAuthSignatureMethod_HMAC_SHA1()
        self._opener = None
        if access_token:
            self.set_access_token(access_token)

    def fetch_request_token(self):
        """
        fetches and return request token
        """
        return self.get_token(self.REQUEST_TOKEN_URL)

    def get_authorize_fb_url(self, token, fb_access_token, callback_url=None):
        """
        creates authorize url for facebook authentication
        """
        token = self._parse_token(token)
        return self.get_authorize_url(
                token,
                authorization_url=self.FB_AUTHORIZATION_URL,
                params={'access_token': fb_access_token},
                callback_url=callback_url,
        )

    def get_authorize_url(self, token, authorization_url=None, params=None, callback_url=None):
        token = self._parse_token(token)
        oauth_request = oauth.OAuthRequest.from_token_and_callback(
                token=token,
                callback=callback_url,
                http_url=authorization_url or self.AUTHORIZATION_URL,
                parameters=params,
        )
        return oauth_request.to_url()

    def fetch_access_token(self, request_token, verifier):
        request_token = self._parse_token(request_token)
        access_token = self.get_token(
                self.ACCESS_TOKEN_URL,
                request_token=request_token,
                verifier=verifier)
        self.set_access_token(access_token)
        return access_token

    def get_token(self, token_url, request_token=None, verifier=None):
        request_token = self._parse_token(request_token)
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            self.consumer,
            token=request_token,
            verifier=verifier,
            http_url=token_url,
        )
        oauth_request.sign_request(self.signature, self.consumer, request_token)
        req = _Request(oauth_request.http_method, token_url, headers=oauth_request.to_header())
        logger.debug("fetching token: %r", req)
        response=urllib2.urlopen(req).read()
        logger.debug("response: %s", response)
        return oauth.OAuthToken.from_string(response)

    def set_access_token(self, access_token):
        self.access_token = self._parse_token(access_token)
        self._opener = urllib2.build_opener(_OAuthHandler(self.consumer, self.access_token))

    def facebook_login(self, fb_access_token):
        request_token = self.fetch_request_token()
        authorize_url = self.get_authorize_fb_url(request_token, fb_access_token)
        logger.debug('facebook authorization url: %s', authorize_url)
        response = urllib2.urlopen(authorize_url).read()
        logger.debug('response: %r', response)
        verifier = dict(cgi.parse_qsl(response)).get('oauth_verifier')
        return self.fetch_access_token(request_token, verifier)

    def do_request(self, method, url, data=None, headers = None):
        if not self._opener:
            raise Exception('access token not set')

        if url.startswith('/'):
            url = self.API_BASE_URL + url

        headers = headers or {}
        if data is not None:
            data = json.dumps(data)
            headers['Content-Type'] = 'application/json'
            headers['Content-Length'] = str(len(data))

        request = _Request(method, url, data, headers)
        return json.loads(self._opener.open(request).read())

    def get(self, url):
        """
        submits GET request
        returns parsed json data (python object)
        """
        return self.do_request('GET', url)

    def put(self, url, data):
        """
        submits PUT request
        data: request parameters (python object, instance of dict usually)
        returns parsed json data (python object)
        """
        return self.do_request('PUT', url, data)

    def post(self, url, data):
        """
        submits POST request
        data: request parameters (python object, instance of dict usually)
        returns parsed json data (python object)
        """
        return self.do_request('POST', url, data)

    def delete(self, url):
        """
        submits DELETE request
        returns parsed json data (python object)
        """
        return self.do_request('DELETE', url)

    @classmethod
    def _parse_token(cls, token):
        if isinstance(token, basestring):
            return oauth.OAuthToken.from_string(token)
        return token

class _OAuthHandler(urllib2.BaseHandler):
    """
    urllib2 opener handler for signing requests using provided consumer and access_token
    """
    def __init__(self, consumer, access_token):
        self.consumer = consumer
        self.access_token = access_token

    def http_request(self, request):
        params = {}
        url = request.get_full_url()
        if '?' in url:
            qs = url.split('?',1)[1]
            params.update(cgi.parse_qsl(qs))
        content_type = request.headers.get('Content-Type')
        if content_type in [None, 'application/x-www-form-urlencoded'] and request.data:
            params.update(cgi.parse_qsl(request.data))
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
             self.consumer, 
             token = self.access_token,
             http_method = request.get_method().upper(), 
             http_url = url, 
             parameters = params)
        oauth_request.sign_request(oauth.OAuthSignatureMethod_HMAC_SHA1(), self.consumer, token = self.access_token)
        oauth_headers = oauth_request.to_header()
        request.headers.update(oauth_headers)
        logger.debug('request: %s', request)
        return request

    def http_response(self, request, response):
        return response

    https_request = http_request
    https_response = http_response

class _Request(urllib2.Request):
    def __init__(self, method, url, *args, **kw):
        self.method = method
        self.url = url
        urllib2.Request.__init__(self, url, *args, **kw)

    def get_method(self):
        return self.method

    def __repr__(self):
        return "<Request %s: %s, headers: %r>" % (self.method, self.url, self.headers)
