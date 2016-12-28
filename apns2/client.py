from enum import Enum

from json import loads, dumps
from hyper import HTTP20Connection as HTTP2
from hyper.tls import init_context

from apns2.errors import exception_class_for_reason
from apns2.payload import Payload

# const
SERVER_ADDR = 'api.push.apple.com'
SERVER_ADDR_SANDBOX = 'api.development.push.apple.com'

PORT = 443
ALTERNATIVE_PORT = 2197


class NotificationPriority(Enum):
    Immediate = '10'
    Delayed = '5'


class APNsClient(object):

    def __init__(self, cert_file, **kargs):
        self.__encoder = None
        if 'json_encoder' in kargs:
            self.__encoder = kargs['json_encoder']

        addr = SERVER_ADDR
        if 'use_sandbox' in kargs and kargs['use_sandbox']:
            addr = SERVER_ADDR_SANDBOX

        port = PORT
        if 'use_alternative_port' in kargs and kargs['use_alternative_port']:
            port = ALTERNATIVE_PORT

        proto = 'h2'
        if 'proto' in kargs:
            proto = kargs['proto'] or 'h2'

        self.__connection = None
        self.__connection_parameters = {
            'server': addr,
            'port': port,
            'ssl_context': {
                'cert_file': cert_file
            },
            'proto': proto
        }

    def send_notification(self, token_hex, notification, **kargs):
        payload = notification
        if isinstance(notification, Payload):
            payload = notification.dict()

        json = dumps(payload, cls=self.__encoder, ensure_ascii=False, separators=(',', ':'))
        headers = get_headers(**kargs)

        with self.__send_request(token, json.encode('utf-8'), headers) as resp:
            raw_data = resp.read().decode('utf-8')

            if resp.status != 200:
                data = loads(raw_data)
                raise exception_class_for_reason(data['reason'])

    @staticmethod
    def get_headers(**kargs):
        priority = NotificationPriority.Immediate
        if 'priority' in kargs:
            kargs['priority'] = kargs['priority']

        headers = {
            'apns-priority': priority.value
        }

        if 'topic' in kargs:
            headers['apns-topic'] = kargs['topic']

        if 'expiration' in kargs:
            headers['apns-expiration'] = "%d" % kargs['expiration']

        return headers

    def __send_request(self, token, payload, headers):
        if not self.__connection:  # Lazy Connecting
            s = self.__connection_parameters['server']
            port = self.__connection_parameters['port']
            cert = self.__connection_parameters['ssl_context']['cert_file']
            pr = self.__connection_parameters['proto']

            ssl = init_context()
            ssl.load_cert_chain(cert)

            self.__connection = HTTP2(s, port, ssl_context=ssl, force_proto=pr)

        url = '/3/device/{}'.format(token)
        stream_id = self.__connection.request('POST', url, payload, headers)
        return self.__connection.get_response(stream_id)
