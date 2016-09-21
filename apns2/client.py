from json import dumps

from tornado import gen
from http2 import SimpleAsyncHTTP2Client
from functools import partial

NOTIFICATION_PRIORITY = dict(immediate='10', delayed='5')


class APNsClient(object):
    def __init__(self, cert_file, key_file, use_sandbox=False, use_alternative_port=False, proto=None, http_client_key=None):
        server = 'api.development.push.apple.com' if use_sandbox else 'api.push.apple.com'
        port = 2197 if use_alternative_port else 443
        cert_options = dict(validate_cert=True, client_cert=cert_file, client_key=key_file)
        self.__http_client = SimpleAsyncHTTP2Client(host=server, port=port, secure=True, cert_options=cert_options, enable_push=True, connect_timeout=2, max_streams=20, http_client_key=http_client_key)
        self.__url_pattern = '/3/device/{token}'
        self.cert_file = cert_file

    def __repr__(self):
        return "APNSClient: {}".format(self.cert_file)

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
        
        futures = []

        for token in tokens:
            url = self.__url_pattern.format(token=token)
            if cb:
                callback = partial(cb, token=token)
            else:
                callback = None
            print('Headers: %s' % headers)
            print('Payload: %s' % json_payload)
            print('Url: %s' % url)
            future = self.__http_client.fetch(url, method='POST', body=json_payload, headers=headers, callback=callback, raise_error=False)
            futures.append(future)

        yield futures
