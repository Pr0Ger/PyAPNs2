# PyAPNs2
Python library for interacting with the Apple Push Notification service (APNs) via HTTP/2 protocol

## Installation

Either download the source from GitHub or use easy_install:

    $ easy_install apns2

## Sample usage

```python
from apns2.client import APNsClient
from apns2.payload import Payload

token_hex = 'b5bb9d8014a0f9b1d61e21e796d78dccdf1352f23cd32812f4850b87'
payload = Payload(alert="Hello World!", sound="default", badge=1)
client = APNsClient('key.pem', use_sandbox=False, use_alternative_port=False)
client.send_notification(token_hex, payload)
```

## Further Info

[iOS Reference Library: Local and Push Notification Programming Guide][a1]

## License

PyAPNs2 is distributed under the terms of the MIT license.

See [LICENSE](LICENSE) file for the complete license details.

[a1]:https://developer.apple.com/library/ios/documentation/NetworkingInternet/Conceptual/RemoteNotificationsPG/Chapters/Introduction.html
