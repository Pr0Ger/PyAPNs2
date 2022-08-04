import collections
import httpx
import json
import logging
from enum import Enum
from typing import Dict, Iterable, Optional, Tuple, Union

from .credentials import TokenCredentials
from .errors import exception_class_for_reason
# We don't generally need to know about the Credentials subclasses except to
# keep the old API, where APNsClient took a cert_file
from .payload import Payload


class NotificationPriority(Enum):
    Immediate = '10'
    Delayed = '5'


class NotificationType(Enum):
    Alert = 'alert'
    Background = 'background'
    VoIP = 'voip'
    Complication = 'complication'
    FileProvider = 'fileprovider'
    MDM = 'mdm'


RequestStream = collections.namedtuple('RequestStream', ['token', 'status', 'reason'])
Notification = collections.namedtuple('Notification', ['token', 'payload'])

DEFAULT_APNS_PRIORITY = NotificationPriority.Immediate
CONCURRENT_STREAMS_SAFETY_MAXIMUM = 1000
MAX_CONNECTION_RETRIES = 3

logger = logging.getLogger(__name__)


class APNsClient(object):
    SANDBOX_SERVER = 'api.development.push.apple.com'
    LIVE_SERVER = 'api.push.apple.com'

    DEFAULT_PORT = 443
    ALTERNATIVE_PORT = 2197

    def __init__(self,
                 credentials: TokenCredentials,
                 use_sandbox: bool = False, use_alternative_port: bool = False, proto: Optional[str] = None,
                 json_encoder: Optional[type] = None, password: Optional[str] = None,
                 proxy_host: Optional[str] = None, proxy_port: Optional[int] = None,
                 heartbeat_period: Optional[float] = None) -> None:

        self.__credentials = credentials
        self._init_connection(use_sandbox, use_alternative_port, proto, proxy_host, proxy_port)

        if heartbeat_period:
            raise NotImplementedError("heartbeat not supported")

        self.__json_encoder = json_encoder

    def _init_connection(self, use_sandbox: bool, use_alternative_port: bool, proto: Optional[str],
                         proxy_host: Optional[str], proxy_port: Optional[int]) -> None:
        self.__server = self.SANDBOX_SERVER if use_sandbox else self.LIVE_SERVER
        self.__port = self.ALTERNATIVE_PORT if use_alternative_port else self.DEFAULT_PORT

    def send_notification(self, token_hex: str, notification: Payload, topic: Optional[str] = None,
                          priority: NotificationPriority = NotificationPriority.Immediate,
                          expiration: Optional[int] = None, collapse_id: Optional[str] = None) -> None:
        with httpx.Client(http2=True) as client:
            status, reason = self.send_notification_sync(token_hex, notification, client, topic, priority, expiration,
                                                         collapse_id)

        if status != 200:
            raise exception_class_for_reason(reason)

    def send_notification_sync(self, token_hex: str, notification: Payload, client: httpx.Client,
                               topic: Optional[str] = None,
                               priority: NotificationPriority = NotificationPriority.Immediate,
                               expiration: Optional[int] = None, collapse_id: Optional[str] = None,
                               push_type: Optional[NotificationType] = None) -> int:
        json_str = json.dumps(notification.dict(), cls=self.__json_encoder, ensure_ascii=False, separators=(',', ':'))
        json_payload = json_str.encode('utf-8')

        headers = {}

        inferred_push_type = None  # type: Optional[str]
        if topic is not None:
            headers['apns-topic'] = topic
            if topic.endswith('.voip'):
                inferred_push_type = NotificationType.VoIP.value
            elif topic.endswith('.complication'):
                inferred_push_type = NotificationType.Complication.value
            elif topic.endswith('.pushkit.fileprovider'):
                inferred_push_type = NotificationType.FileProvider.value
            elif any([
                notification.alert is not None,
                notification.badge is not None,
                notification.sound is not None,
            ]):
                inferred_push_type = NotificationType.Alert.value
            else:
                inferred_push_type = NotificationType.Background.value

        if push_type:
            inferred_push_type = push_type.value

        if inferred_push_type:
            headers['apns-push-type'] = inferred_push_type

        if priority != DEFAULT_APNS_PRIORITY:
            headers['apns-priority'] = priority.value

        if expiration is not None:
            headers['apns-expiration'] = '%d' % expiration

        auth_header = self.__credentials.get_authorization_header(topic)
        if auth_header is not None:
            headers['authorization'] = auth_header

        if collapse_id is not None:
            headers['apns-collapse-id'] = collapse_id

        url = '/3/device/{}'.format(token_hex)
        response = client.post(f"https://{self.__server}:{self.__port}{url}", headers=headers, data=json_payload)
        return response.status_code, response.text

    def get_notification_result(self, status: int, reason: str) -> Union[str, Tuple[str, str]]:
        """
        Get result for specified stream
        The function returns: 'Success' or 'failure reason'
        """
        if status == 200:
            return 'Success'
        else:
            return reason

    def send_notification_batch(self, notifications: Iterable[Notification], topic: Optional[str] = None,
                                priority: NotificationPriority = NotificationPriority.Immediate,
                                expiration: Optional[int] = None, collapse_id: Optional[str] = None,
                                push_type: Optional[NotificationType] = None) -> Dict[str, Union[str, Tuple[str, str]]]:
        """
        Send a notification to a list of tokens in batch.

        The function returns a dictionary mapping each token to its result. The result is "Success"
        if the token was sent successfully, or the string returned by APNs in the 'reason' field of
        the response, if the token generated an error.
        """
        results = {}

        # Loop over notifications
        with httpx.Client(http2=True) as client:
            for next_notification in notifications:
                logger.info('Sending to token %s', next_notification.token)
                status, reason = self.send_notification_sync(next_notification.token, next_notification.payload, client,
                                                             topic, priority, expiration, collapse_id, push_type)
                result = self.get_notification_result(status, reason)
                logger.info('Got response for %s: %s', next_notification.token, result)
                results[next_notification.token] = result

        return results

    def connect(self) -> None:
        """
        Establish a connection to APNs. If already connected, the function does nothing. If the
        connection fails, the function retries up to MAX_CONNECTION_RETRIES times.
        """
        # Not needed for HTTPX
        logger.info('APNsClient.connect called')
