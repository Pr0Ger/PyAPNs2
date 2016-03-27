# pylint: disable=protected-access

from unittest import TestCase
import contextlib
import logging

try:
    # Python 3
    from unittest.mock import MagicMock, Mock, patch
except ImportError:
    # Python 2
    from mock import MagicMock, Mock, patch

from apns2.client import APNsClient, CONCURRENT_STREAMS_SAFETY_MAXIMUM, Notification
from apns2.errors import ConnectionFailed
from apns2.payload import Payload


class ClientTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        # Ignore all log messages so that test output is not cluttered.
        logging.basicConfig(level=logging.CRITICAL)
        cls.tokens = ['%064x' % i for i in range(10000)]
        cls.payload = Payload(alert='Test alert')
        cls.notifications = [Notification(token=token, payload=cls.payload) for token in cls.tokens]
        cls.topic = 'com.example.App'

    def setUp(self):
        self.open_streams = 0
        self.max_open_streams = 0
        self.mock_results = None
        self.next_stream_id = 0

        with patch('apns2.client.HTTP20Connection') as mock_connection_constructor, patch('apns2.client.init_context'):
            self.mock_connection = MagicMock()
            self.mock_connection.get_response.side_effect = self.mock_get_response
            self.mock_connection.request.side_effect = self.mock_request
            self.mock_connection._conn.__enter__.return_value = self.mock_connection._conn
            self.mock_connection._conn.remote_settings.max_concurrent_streams = 500
            mock_connection_constructor.return_value = self.mock_connection
            self.client = APNsClient(cert_file=None)

    @contextlib.contextmanager
    def mock_get_response(self, stream_id):
        self.open_streams -= 1
        if self.mock_results:
            reason = self.mock_results[stream_id]
            response = Mock(status=200 if reason == 'Success' else 400)
            response.read.return_value = ('{"reason": "%s"}' % reason).encode('utf-8')
            yield response
        else:
            yield Mock(status=200)

    def mock_request(self, *dummy_args):
        self.open_streams += 1
        if self.open_streams > self.max_open_streams:
            self.max_open_streams = self.open_streams

        stream_id = self.next_stream_id
        self.next_stream_id += 1
        return stream_id

    def test_send_notification_batch_returns_results_in_order(self):
        results = self.client.send_notification_batch(self.notifications, self.topic)
        expected_results = {token: 'Success' for token in self.tokens}
        self.assertEqual(results, expected_results)

    def test_send_notification_batch_respects_max_concurrent_streams_from_server(self):
        self.client.send_notification_batch(self.notifications, self.topic)
        self.assertEqual(self.max_open_streams, 500)

    def test_send_notification_batch_overrides_server_max_concurrent_streams_if_too_large(self):
        self.mock_connection._conn.remote_settings.max_concurrent_streams = 5000
        self.client.send_notification_batch(self.notifications, self.topic)
        self.assertEqual(self.max_open_streams, CONCURRENT_STREAMS_SAFETY_MAXIMUM)

    def test_send_notification_batch_overrides_server_max_concurrent_streams_if_too_small(self):
        self.mock_connection._conn.remote_settings.max_concurrent_streams = 0
        self.client.send_notification_batch(self.notifications, self.topic)
        self.assertEqual(self.max_open_streams, 1)

    def test_send_notification_batch_reports_different_results(self):
        self.mock_results = (
            ['BadDeviceToken'] * 1000 + ['Success'] * 1000 + ['DeviceTokenNotForTopic'] * 2000 +
            ['Success'] * 1000 + ['BadDeviceToken'] * 500 + ['PayloadTooLarge'] * 4500
        )
        results = self.client.send_notification_batch(self.notifications, self.topic)
        expected_results = dict(zip(self.tokens, self.mock_results))
        self.assertEqual(results, expected_results)

    def test_send_empty_batch_does_nothing(self):
        self.client.send_notification_batch([], self.topic)
        self.assertEqual(self.mock_connection.request.call_count, 0)

    def test_connect_establishes_connection(self):
        self.client.connect()
        self.mock_connection.connect.assert_called_once_with()

    def test_connect_retries_failed_connection(self):
        self.mock_connection.connect.side_effect = [RuntimeError, RuntimeError, None]
        self.client.connect()
        self.assertEqual(self.mock_connection.connect.call_count, 3)

    def test_connect_stops_on_reaching_max_retries(self):
        self.mock_connection.connect.side_effect = [RuntimeError] * 4
        with self.assertRaises(ConnectionFailed):
            self.client.connect()

        self.assertEqual(self.mock_connection.connect.call_count, 3)
