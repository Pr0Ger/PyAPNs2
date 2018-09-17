# -*- coding: utf-8 -*-
from builtins import next
from builtins import object
import collections
import json
import logging
from enum import Enum
from json import dumps
from hyper import HTTP20Connection
from hyper.http20.exceptions import StreamResetError
from hyper.tls import init_context
import time
import jwt

from .errors import ConnectionFailed, exception_class_for_reason


class NotificationPriority(Enum):
    Immediate = '10'
    Delayed = '5'

RequestStream = collections.namedtuple('RequestStream', ['stream_id', 'token'])
Notification = collections.namedtuple('Notification', ['token', 'payload'])

DEFAULT_APNS_PRIORITY = NotificationPriority.Immediate
CONCURRENT_STREAMS_SAFETY_MAXIMUM = 1000
MAX_CONNECTION_RETRIES = 3

logger = logging.getLogger(__name__)

# class Notification(object):
#     def __init__(self, token, payload):
#         self.token = token
#         self.payload = payload


class APNsClient(object):
    def __init__(self, cert_file=None, key_file=None, team=None, key_id=None, use_sandbox=False, use_alternative_port=False, http_client_key=None, proto=None, json_encoder=None, request_timeout=20, pool_size=5, connect_timeout=20):
        server = 'api.development.push.apple.com' if use_sandbox else 'api.push.apple.com'
        port = 2197 if use_alternative_port else 443
        self._auth_token = None
        self.auth_token_expired = False
        self.json_payload = None
        self.headers = None
        ssl_context = None

        if cert_file and key_file:
            ssl_context = init_context()
            ssl_context.load_cert_chain(cert_file)
            self.auth_type = 'cert'
        elif team and key_id and key_file:
            self._team = team

            with open(key_file, 'r') as tmp:
                self._auth_key = tmp.read()

            self._key_id = key_id
            self._auth_token = self.get_auth_token()
            self._header_format = 'bearer %s'
            self.auth_type = 'token'

        self.cert_file = cert_file
        self.__url_pattern = '/3/device/{token}'
        
        self.__connection = HTTP20Connection(server, port, ssl_context=ssl_context, force_proto=proto or 'h2')
        self.__json_encoder = json_encoder
        self.__max_concurrent_streams = None
        self.__previous_server_max_concurrent_streams = None
        self.open_streams = collections.deque()

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
                iat=int(time.time())
            )
            self._auth_token = jwt.encode(claim, self._auth_key, algorithm='ES256', headers={'kid': self._key_id})
            self.auth_token_expired = False
        return self._auth_token

    def prepare_payload(self, notification):
        return dumps(notification.dict(), cls=self.__json_encoder, ensure_ascii=False, separators=(',', ':')).encode('utf-8')

    def prepare_headers(self, priority, topic, expiration, collapse_id=None):
        headers = {}

        if priority != DEFAULT_APNS_PRIORITY:
            headers['apns-priority'] = priority.value

        # headers = {
        #     'apns-priority': priority
        # }

        if topic:
            headers['apns-topic'] = topic

        if expiration is not None:
            headers['apns-expiration'] = "%d" % expiration

        if self.auth_type == 'token':
            headers['Authorization'] = self._header_format % self.get_auth_token().decode('ascii')

        if collapse_id:
            headers['apns-collapse-id'] = collapse_id

        return headers

    def prepare_request(self, notification, priority=NotificationPriority.Immediate, topic=None, expiration=None, collapse_id=None):
        json_payload = self.prepare_payload(notification)
        headers = self.prepare_headers(priority, topic, expiration, collapse_id)
        return dict(json_payload=json_payload, headers=headers)


    def send_notification(self, token_hex, notification, topic, priority=NotificationPriority.Immediate,
                          expiration=None):
        stream_id = self.send_notification_async(token_hex, notification, topic, priority, expiration)
        result = self.get_notification_result(stream_id)
        if result != 'Success':
            raise exception_class_for_reason(result)

    def send_notification_async(self, token_hex, priority=NotificationPriority.Immediate,
                                expiration=None):

        url = self.__url_pattern.format(token=token_hex)
        stream_id = self.__connection.request('POST', url, self.json_payload, self.headers)
        return stream_id


    def get_notification_result(self, stream_id):
        with self.__connection.get_response(stream_id) as response:
            if response.status == 200:
                return (200, 'Success')
            else:
                reason = u''
                raw_data = response.read().decode('utf-8')
                data = json.loads(raw_data)
                reason = data.get('reason')
                return (response.status, reason)

    def send_notification_batch(self, tokens, notification, headers=None, priority=NotificationPriority.Immediate, topic=None, expiration=None, collapse_id=None, cb=None):
        '''
        Send a notification to a list of tokens in batch. Instead of sending a synchronous request
        for each token, send multiple requests concurrently. This is done on the same connection,
        using HTTP/2 streams (one request per stream).

        APNs allows many streams simultaneously, but the number of streams can vary depending on
        server load. This method reads the SETTINGS frame sent by the server to figure out the
        maximum number of concurrent streams. Typically, APNs reports a maximum of 500.

        The function returns a dictionary mapping each token to its result. The result is "Success"
        if the token was sent successfully, or the string returned by APNs in the 'reason' field of
        the response, if the token generated an error.
        '''
        self.json_payload = self.prepare_payload(notification)
        
        self.headers = self.prepare_headers(priority, topic, expiration)

        token_iterator = iter(tokens)
        next_token = next(token_iterator, None)
        # Make sure we're connected to APNs, so that we receive and process the server's SETTINGS
        # frame before starting to send notifications.
        self.connect()

        results = {}
        force_results = False

        # Loop on the tokens, sending as many requests as possible concurrently to APNs.
        # When reaching the maximum concurrent streams limit, wait for a response before sending
        # another request.
        while len(self.open_streams) > 0 or next_token is not None or force_results:
            # Update the max_concurrent_streams on every iteration since a SETTINGS frame can be
            # sent by the server at any time.
            self.update_max_concurrent_streams()
            if self.should_send_notification(next_token, force_results):
                try:
                    # logger.debug('Sending to token %s', next_token)
                    stream_id = self.send_notification_async(next_token)
                    self.open_streams.append(RequestStream(stream_id, next_token))

                    next_token = next(token_iterator, None)
                    if next_token is None:
                        # No tokens remaining. Proceed to get results for pending requests.
                        logger.debug('Finished sending all tokens, waiting for pending requests.')
                except Exception as err:
                    force_results = True
                    logger.error('Error while sending to APNS: %s', err)

            else:
                # We have at least one request waiting for response (otherwise we would have either
                # sent new requests or exited the while loop.) Wait for the first outstanding stream
                # to return a response.
                pending_stream = self.open_streams.popleft()
                try:
                    result = (None, None)
                    result = self.get_notification_result(pending_stream.stream_id)
                    # logger.debug('Got response for %s: %s', pending_stream.token, result)
                except StreamResetError as err:
                    result = (666, 'WTF')

                except Exception as err:
                    logger.error('Error %s while getting result for token %s and stream_id %s', err, pending_stream.token, pending_stream.stream_id)
                    # @TODO: resend token!
                finally:
                    if cb is not None:
                        cb(pending_stream.token, result)
                    else:
                        results[pending_stream.token] = result

                if len(self.open_streams) == 0 and force_results:  # получили все результаты и надо переподключиться
                    self.__connection.close()
                    self.__previous_server_max_concurrent_streams = None
                    self.connect()
                    force_results = False
                    logger.info('Try to reconnect and resend')

        return results

    def should_send_notification(self, notification, force_results=False):
        return not force_results and (notification is not None and len(self.open_streams) < self.__max_concurrent_streams)

    def update_max_concurrent_streams(self):
        # Get the max_concurrent_streams setting returned by the server.
        # The max_concurrent_streams value is saved in the H2Connection instance that must be
        # accessed using a with statement in order to acquire a lock.
        # pylint: disable=protected-access
        with self.__connection._conn as connection:
            max_concurrent_streams = connection.remote_settings.max_concurrent_streams
            # logger.debug('connection.remote_settings.max_concurrent_streams=%s', connection.remote_settings.max_concurrent_streams)

        if max_concurrent_streams == self.__previous_server_max_concurrent_streams:
            # The server hasn't issued an updated SETTINGS frame.
            return

        self.__previous_server_max_concurrent_streams = max_concurrent_streams
        # Handle and log unexpected values sent by APNs, just in case.
        if max_concurrent_streams > CONCURRENT_STREAMS_SAFETY_MAXIMUM:
            logger.warning('APNs max_concurrent_streams too high (%s), resorting to default maximum (%s)',
                           max_concurrent_streams, CONCURRENT_STREAMS_SAFETY_MAXIMUM)
            self.__max_concurrent_streams = CONCURRENT_STREAMS_SAFETY_MAXIMUM
        elif max_concurrent_streams < 1:
            logger.warning('APNs reported max_concurrent_streams less than 1 (%s), using value of 1',
                           max_concurrent_streams)
            self.__max_concurrent_streams = 1
        else:
            logger.info('APNs set max_concurrent_streams to %s', max_concurrent_streams)
            self.__max_concurrent_streams = max_concurrent_streams

    def connect(self):
        '''
        Establish a connection to APNs. If already connected, the function does nothing. If the
        connection fails, the function retries up to MAX_CONNECTION_RETRIES times.
        '''
        retries = 0
        while retries < MAX_CONNECTION_RETRIES:
            try:
                self.__connection.connect()
                # logger.debug('Connected to APNs')
                return
            except Exception:  # pylint: disable=broad-except
                retries += 1
                logger.exception('Failed connecting to APNs (attempt %s of %s)', retries, MAX_CONNECTION_RETRIES)

        raise ConnectionFailed()
