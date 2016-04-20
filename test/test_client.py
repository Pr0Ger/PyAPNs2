from collections import Counter
from mock import Mock, patch
from unittest import TestCase
import logging

import hyper
import hyper.tls

from apns2.client import APNsClient, CONCURRENT_STREAMS_SAFETY_MAXIMUM
from apns2.payload import Payload

class ClientTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        logging.basicConfig()
        cls.tokens = ["%064x" % i for i in range(10000)]
        cls.notification = Payload(alert="Hello, world!")
        cls.topic = "com.example.App"

    
    def setUp(self):
        self.open_streams = 0
        self.max_open_streams = 0
        
        with patch("apns2.client.HTTP20Connection") as mock_connection_constructor, \
            patch("apns2.client.init_context"):
            self.mock_connection = Mock()
            self.mock_connection.get_response.side_effect = self.mock_get_response
            self.mock_connection.request.side_effect = self.mock_request
            self.mock_connection.remote_settings.max_concurrent_streams = 500
            mock_connection_constructor.return_value = self.mock_connection
            self.client = APNsClient(cert_file=None)
            
    def mock_get_response(self, *dummy_args):
        self.open_streams -= 1
        return Mock(status=200)
    
    def mock_request(self, *dummy_args):
        self.open_streams += 1
        if self.open_streams > self.max_open_streams:
            self.max_open_streams = self.open_streams
        
    def test_send_notification_batch(self):
        results = self.client.send_notification_batch(self.tokens, self.notification, self.topic)
        self.assertEqual(results, Counter({"Success": 10000}))

    def test_send_notification_batch_respects_max_concurrent_streams_from_server(self):
        self.client.send_notification_batch(self.tokens, self.notification, self.topic)
        self.assertEqual(self.max_open_streams, 500)

    def test_send_notification_batch_overrides_server_max_concurrent_streams_if_too_large(self):
        self.mock_connection.remote_settings.max_concurrent_streams = 5000
        self.client.send_notification_batch(self.tokens, self.notification, self.topic)
        self.assertEqual(self.max_open_streams, CONCURRENT_STREAMS_SAFETY_MAXIMUM)
        
    def test_send_notification_batch_overrides_server_max_concurrent_streams_if_too_small(self):
        self.mock_connection.remote_settings.max_concurrent_streams = 0
        self.client.send_notification_batch(self.tokens, self.notification, self.topic)
        self.assertEqual(self.max_open_streams, 1)
