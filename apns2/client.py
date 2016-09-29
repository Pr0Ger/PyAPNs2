from json import dumps
import time

from tornado import gen
from http2 import SimpleAsyncHTTP2Client
import jwt


NOTIFICATION_PRIORITY = dict(immediate='10', delayed='5')


class APNsClient(object):
    auth_type = None
    def __init__(self, cert_file=None, key_file=None, team=None, key_id=None, use_sandbox=False, use_alternative_port=False, proto=None, http_client_key=None, connect_timeout=2):
        server = 'api.development.push.apple.com' if use_sandbox else 'api.push.apple.com'
        port = 2197 if use_alternative_port else 443
        self._auth_token = None
        self.auth_token_expired = False
        cert_options = None

        # authenticate with individual certificates for every app
        if cert_file and key_file:
            cert_options = dict(validate_cert=True, client_cert=cert_file, client_key=key_file)
            self.auth_type = 'cert'
        # auth with universal JWT token
        elif team and key_id and key_file:
            self._team = team

            with open(key_file, 'r') as tmp:
                self._auth_key = tmp.read()

            self._key_id = key_id
            self._auth_token = self.get_auth_token()
            self._header_format = 'bearer %s'
            self.auth_type = 'token'


        self.__http_client = SimpleAsyncHTTP2Client(
            host=server,
            port=port,
            secure=True,
            cert_options=cert_options,
            enable_push=False,
            connect_timeout=connect_timeout,
            max_streams=100,
            http_client_key=http_client_key
        )
        self.__url_pattern = '/3/device/{token}'
        self.cert_file = cert_file

    def __repr__(self):
        uid = None
        if self.auth_type == 'cert':
            uid = self.cert_file
        elif self.auth_type == 'token':
            uid = self._key_id
        return "APNSClient: {}".format(uid)

    def get_auth_token(self):
        if not self._auth_token or self.auth_token_expired:
            claim = dict(
                iss=self._team,
                iat=int(time.time())  #  @TODO regenerate it from time to time (interval???)
            )
            self._auth_token = jwt.encode(claim, self._auth_key, algorithm='ES256', headers={'kid': self._key_id})
            self.auth_token_expired = False
        return self._auth_token

    @gen.coroutine
    def send_notifications(self, tokens, notification, priority=NOTIFICATION_PRIORITY['immediate'], topic=None, expiration=None, cb=None):
        json_payload = dumps(notification.dict(), ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        headers = {
            'apns-priority': priority
        }
        if topic:
            headers['apns-topic'] = topic

        if expiration is not None:
            headers['apns-expiration'] = "%d" % expiration

        if self.auth_type == 'token':
            headers['Authorization'] = self._header_format % self.get_auth_token().decode('ascii')
        
        futures = []

        for token in tokens:
            url = self.__url_pattern.format(token=token)
            future = self.__http_client.fetch(url, method='POST', body=json_payload, headers=headers, callback=cb, raise_error=False)
            futures.append(future)

        yield futures
