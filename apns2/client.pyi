from typing import Optional

from apns2.client import NotificationPriority
from apns2.payload import Payload


class APNsClient(object):
    def __init__(self,
                 cert_file: str,
                 use_sandbox: bool = False,
                 use_alternative_port: bool = False) -> None: ...

    def send_notification(self,
                          token_hex: str,
                          notification: Payload,
                          priority: NotificationPriority = NotificationPriority.Immediate,
                          topic: Optional[str] = None,
                          expiration: Optional[int] = None) -> None: ...
