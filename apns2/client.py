from enum import Enum

from json import loads, dumps
from hyper import HTTP20Connection
from hyper.tls import init_context

from apns2.errors import exception_class_for_reason
from apns2.payload import Payload

# const
SERVER_ADDR = 'api.push.apple.com'
SERVER_ADDR_DEV = 'api.development.push.apple.com'

PORT = 443
ALTERNATIVE_PORT = 2197


class NotificationPriority(Enum):
    Immediate = '10'
    Delayed = '5'


class APNsClient(object):

    def __init__(self, cert_file, use_sandbox=False, use_alternative_port=False, proto=None, json_encoder=None):
        self.__json_encoder = json_encoder

        self.__connection = None
        self.__connection_parameters = {
            'server': SERVER_ADDR_DEV if use_sandbox else SERVER_ADDR,
            'port': ALTERNATIVE_PORT if use_alternative_port else PORT,
            'ssl_context': {
                'cert_file': cert_file
            },
            'proto': proto or 'h2'
        }

    def send_notification(self, token_hex, notification, priority=NotificationPriority.Immediate, topic=None, expiration=None):
        payload = notification
        if isinstance(notification, Payload): 
            payload = notification.dict() 

        json_payload = dumps(payload, cls=self.__json_encoder, ensure_ascii=False, separators=(',', ':')).encode('utf-8')

        headers = {
            'apns-priority': priority.value
        }
        if topic:
            headers['apns-topic'] = topic

        if expiration:
            headers['apns-expiration'] = "%d" % expiration

        with self.__send_request(token_hex, json_payload, headers) as resp:
            raw_data = resp.read().decode('utf-8')

            if resp.status != 200:
                data = loads(raw_data)
                raise exception_class_for_reason(data['reason'])

    def __send_request(self, token, payload, headers):
        if not self.__connection:  # Lazy Connecting
            server = self.__connection_parameters['server']
            port = self.__connection_parameters['port']
            cert = self.__connection_parameters['ssl_context']['cert_file']
            proto = self.__connection_parameters['proto']

            ssl_context = init_context()
            ssl_context.load_cert_chain(cert)

            self.__connection = HTTP20Connection(server, port, ssl_context=ssl_context, force_proto=proto)

        url = '/3/device/{}'.format(token_hex)
        stream_id = self.__connection.request('POST', url, json_payload, headers)
        return self.__connection.get_response(stream_id)
