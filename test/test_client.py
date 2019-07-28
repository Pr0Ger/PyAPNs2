import contextlib
from unittest.mock import MagicMock, Mock, patch

import pytest

from apns2.client import APNsClient, CertificateCredentials, CONCURRENT_STREAMS_SAFETY_MAXIMUM, Notification
from apns2.errors import ConnectionFailed
from apns2.payload import Payload

TOPIC = 'com.example.App'


@pytest.fixture(scope='session')
def tokens():
    return ['%064x' % i for i in range(1000)]


@pytest.fixture(scope='session')
def notifications(tokens):
    payload = Payload(alert='Test alert')
    return [Notification(token=token, payload=payload) for token in tokens]


@patch('apns2.credentials.init_context')
@pytest.fixture
def client(mock_connection):
    with patch('apns2.credentials.HTTP20Connection') as mock_connection_constructor:
        mock_connection_constructor.return_value = mock_connection
        return APNsClient(credentials=CertificateCredentials())


@pytest.fixture
def mock_connection():
    mock_connection = MagicMock()
    mock_connection.__max_open_streams = 0
    mock_connection.__open_streams = 0
    mock_connection.__mock_results = None
    mock_connection.__next_stream_id = 0

    @contextlib.contextmanager
    def mock_get_response(stream_id):
        mock_connection.__open_streams -= 1
        if mock_connection.__mock_results:
            reason = mock_connection.__mock_results[stream_id]
            response = Mock(status=200 if reason == 'Success' else 400)
            response.read.return_value = ('{"reason": "%s"}' % reason).encode('utf-8')
            yield response
        else:
            yield Mock(status=200)

    def mock_request(*_args):
        mock_connection.__open_streams += 1
        mock_connection.__max_open_streams = max(mock_connection.__open_streams, mock_connection.__max_open_streams)

        stream_id = mock_connection.__next_stream_id
        mock_connection.__next_stream_id += 1
        return stream_id

    mock_connection.get_response.side_effect = mock_get_response
    mock_connection.request.side_effect = mock_request
    mock_connection._conn.__enter__.return_value = mock_connection._conn
    mock_connection._conn.remote_settings.max_concurrent_streams = 500

    return mock_connection


def test_connect_establishes_connection(client, mock_connection):
    client.connect()
    mock_connection.connect.assert_called_once_with()


def test_connect_retries_failed_connection(client, mock_connection):
    mock_connection.connect.side_effect = [RuntimeError, RuntimeError, None]
    client.connect()
    assert mock_connection.connect.call_count == 3


def test_connect_stops_on_reaching_max_retries(client, mock_connection):
    mock_connection.connect.side_effect = [RuntimeError] * 4
    with pytest.raises(ConnectionFailed):
        client.connect()

    assert mock_connection.connect.call_count == 3


def test_send_empty_batch_does_nothing(client, mock_connection):
    client.send_notification_batch([], TOPIC)
    assert mock_connection.request.call_count == 0


def test_send_notification_batch_returns_results_in_order(client, mock_connection, tokens, notifications):
    results = client.send_notification_batch(notifications, TOPIC)
    expected_results = {token: 'Success' for token in tokens}
    assert results == expected_results


def test_send_notification_batch_respects_max_concurrent_streams_from_server(client, mock_connection, tokens,
                                                                             notifications):
    client.send_notification_batch(notifications, TOPIC)
    assert mock_connection.__max_open_streams == 500


def test_send_notification_batch_overrides_server_max_concurrent_streams_if_too_large(client, mock_connection, tokens,
                                                                                      notifications):
    mock_connection._conn.remote_settings.max_concurrent_streams = 5000
    client.send_notification_batch(notifications, TOPIC)
    assert mock_connection.__max_open_streams == CONCURRENT_STREAMS_SAFETY_MAXIMUM


def test_send_notification_batch_overrides_server_max_concurrent_streams_if_too_small(client, mock_connection, tokens,
                                                                                      notifications):
    mock_connection._conn.remote_settings.max_concurrent_streams = 0
    client.send_notification_batch(notifications, TOPIC)
    assert mock_connection.__max_open_streams == 1


def test_send_notification_batch_reports_different_results(client, mock_connection, tokens,
                                                           notifications):
    mock_connection.__mock_results = (
            ['BadDeviceToken'] * 1000 + ['Success'] * 1000 + ['DeviceTokenNotForTopic'] * 2000 +
            ['Success'] * 1000 + ['BadDeviceToken'] * 500 + ['PayloadTooLarge'] * 4500
    )
    results = client.send_notification_batch(notifications, TOPIC)
    expected_results = dict(zip(tokens, mock_connection.__mock_results))
    assert results == expected_results
