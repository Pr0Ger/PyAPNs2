from typing import Any, Dict, List, Optional, Union


class PayloadAlert(object):
    def __init__(self,
                 title: Optional[str] = None,
                 title_localized_key: Optional[str] = None,
                 title_localized_args: Optional[List[str]] = None,
                 body: Optional[str] = None,
                 body_localized_key: Optional[str] = None,
                 body_localized_args: Optional[List[str]] = None,
                 action_localized_key: Optional[str] = None,
                 action: Optional[str] = None,
                 launch_image: Optional[str] = None
                 ) -> None: ...

    def dict(self) -> Dict[str, Any]: ...


class Payload(object):
    def __init__(self,
                 alert: Union[PayloadAlert, str, None] = None,
                 badge: Optional[int] = None,
                 sound: Optional[str] = None,
                 content_available: Optional[bool] = None,
                 category: Optional[str] = None,
                 custom: Optional[Dict[str, Any]] = None) -> None: ...

    def dict(self) -> Dict[str, Any]: ...
