import collections
import json
import logging
from enum import Enum

from hyper import HTTP20Connection
from hyper.tls import init_context

from .errors import exception_class_for_reason

class NotificationPriority(Enum):
    Immediate = '10'
    Delayed = '5'

DEFAULT_APNS_PRIORITY = NotificationPriority.Immediate
CONCURRENT_STREAMS_SAFETY_MAXIMUM = 1000

logger = logging.getLogger(__name__)

class APNsClient(object):
    def __init__(self, cert_file, use_sandbox=False, use_alternative_port=False):
        server = 'api.development.push.apple.com' if use_sandbox else 'api.push.apple.com'
        port = 2197 if use_alternative_port else 443
        ssl_context = init_context()
        ssl_context.load_cert_chain(cert_file)
        self._connection = HTTP20Connection(server, port, ssl_context=ssl_context)
        self._max_concurrent_streams = None
        self._previous_server_max_concurrent_streams = None

    def send_notification(
        self,
        token_hex,
        notification,
        topic,
        priority=NotificationPriority.Immediate
    ):
        stream_id = self.send_notification_async(token_hex, notification, topic, priority)
        result = self.get_notification_result(stream_id)
        if result != 'Success':
            raise exception_class_for_reason(result)

    def send_notification_async(
        self,
        token_hex,
        notification,
        topic,
        priority=NotificationPriority.Immediate
    ):
        json_payload = json.dumps(
            notification.dict(),
            ensure_ascii=False,
            separators=(',', ':')
        ).encode('utf-8')

        headers = {'apns-topic': topic}
        if priority != DEFAULT_APNS_PRIORITY:
            headers['apns-priority'] = priority.value

        url = '/3/device/{}'.format(token_hex)
        stream_id = self._connection.request('POST', url, json_payload, headers)
        return stream_id

    def get_notification_result(self, stream_id):
        response = self._connection.get_response(stream_id)
        if response.status == 200:
            return 'Success'
        else:
            raw_data = response.read().decode('utf-8')
            data = json.loads(raw_data)
            return data['reason']

    def send_notification_batch(
        self,
        tokens,
        notification,
        topic,
        priority=NotificationPriority.Immediate
    ):
        """
        Send a notification to a list of tokens in batch. Instead of sending a synchronous request
        for each token, send multiple requests concurrently. This is done on the same connection,
        using HTTP/2 streams (one request per stream).

        APNs allows many streams simultaneously, but the number of streams can vary depending on
        server load. This method reads the SETTINGS frame sent by the server to figure out the
        maximum number of concurrent streams. Typically, APNs reports a maximum of 500.
        """
        # Make sure we're connected to APNs, so that we receive and process the server's SETTINGS
        # frame before starting to send notifications.
        self._connection.connect()
        result_counter = collections.Counter()
        open_streams = collections.deque()
        token_iterator = iter(tokens)
        next_token = next(token_iterator)
        # Loop on the tokens, sending as many requests as possible concurrently to APNs.
        # When reaching the maximum concurrent streams limit, wait for a response before sending
        # another request.
        while open_streams or next_token:
            # Update the max_concurrent_streams on every iteration since a SETTINGS frame can be
            # sent by the server at any time.
            self.update_max_concurrent_streams()
            if next_token and len(open_streams) < self._max_concurrent_streams:
                logger.info("Sending to token %s", next_token)
                stream_id = self.send_notification_async(next_token, notification, topic, priority)
                open_streams.append((stream_id, next_token))

                try:
                    next_token = next(token_iterator)
                except StopIteration:
                    # No tokens remaining. Proceed to get results for pending requests.
                    logger.info("Finished sending all tokens, waiting for pending requests.")
                    next_token = None
            else:
                # We have at least one request waiting for response (otherwise we would have either
                # sent new requests or exited the while loop.)
                assert open_streams
                # Wait for the first outstanding stream to return a response.
                stream_id, token = open_streams.popleft()
                result = self.get_notification_result(stream_id)
                logger.info("Got response for %s: %s", token, result)
                result_counter[result] += 1

        return result_counter

    def update_max_concurrent_streams(self):
        # Get the max_concurrent_streams setting returned by the server.
        max_concurrent_streams = self._connection.remote_settings.max_concurrent_streams
        if max_concurrent_streams == self._previous_server_max_concurrent_streams:
            # The server hasn't issued an updated SETTINGS frame.
            return
        
        self._previous_server_max_concurrent_streams = max_concurrent_streams
        # Handle and log unexpected values sent by APNs, just in case.
        if max_concurrent_streams > CONCURRENT_STREAMS_SAFETY_MAXIMUM:
            logger.warning(
                "APNs max_concurrent_streams too high (%s), resorting to default maximum (%s)",
                max_concurrent_streams,
                CONCURRENT_STREAMS_SAFETY_MAXIMUM
            )
            self._max_concurrent_streams = CONCURRENT_STREAMS_SAFETY_MAXIMUM
        elif max_concurrent_streams < 1:
            logger.warning(
                "APNs reported max_concurrent_streams less than 1 (%s), using value of 1",
                max_concurrent_streams
            )
            self._max_concurrent_streams = 1
        else:
            logger.info("APNs set max_concurrent_streams to %s", max_concurrent_streams)
            self._max_concurrent_streams = max_concurrent_streams
