from enum import Enum

from json import loads, dumps
from hyper import HTTP20Connection as HTTP2
from hyper.tls import init_context

from apns2.errors import exception_class_for_reason
from apns2.payload import Payload

# const
SERVER_ADDR = 'api.push.apple.com'
SANDBOX_ADDR = 'api.development.push.apple.com'

PORT = 443
ALTERNATIVE_PORT = 2197


class NotificationPriority(Enum):
    Immediate = '10'
    Delayed = '5'


class APNsClient(object):

    def __init__(self,
                 cert_file,
                 use_sandbox=False,
                 use_alternative_port=False,
                 proto=None,
                 json_encoder=None
                 ):

        self.__encoder = json_encoder
        self.__connection = None
        self.__connection_parameters = {
            'server': SANDBOX_ADDR if use_sandbox else SERVER_ADDR,
            'port': ALTERNATIVE_PORT if use_alternative_port else PORT,
            'ssl_context': {
                'cert_file': cert_file
            },
            'proto': proto or 'h2'
        }

    def send_notification(self,
                          token_hex,
                          notification,
                          priority=NotificationPriority.Immediate,
                          topic=None,
                          expiration=None
                          ):
    
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
