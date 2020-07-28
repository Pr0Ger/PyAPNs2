# PyAPNs2

[![PyPI version](https://img.shields.io/pypi/v/apns2.svg)](https://pypi.python.org/pypi/apns2)
[![PyPI version](https://img.shields.io/pypi/pyversions/apns2.svg)](https://pypi.python.org/pypi/apns2)
[![Build Status](https://drone.pr0ger.dev/api/badges/Pr0Ger/PyAPNs2/status.svg)](https://drone.pr0ger.dev/Pr0Ger/PyAPNs2)

Python library for interacting with the Apple Push Notification service (APNs) via HTTP/2 protocol

## Installation

Either download the source from GitHub or use pip:

    $ pip install apns2

## Sample usage

```python
from apns2.client import APNsClient
from apns2.payload import Payload

token_hex = 'b5bb9d8014a0f9b1d61e21e796d78dccdf1352f23cd32812f4850b87'
payload = Payload(alert="Hello World!", sound="default", badge=1)
topic = 'com.example.App'
client = APNsClient('key.pem', use_sandbox=False, use_alternative_port=False)
client.send_notification(token_hex, payload, topic)

# To send multiple notifications in a batch
Notification = collections.namedtuple('Notification', ['token', 'payload'])
notifications = [Notification(payload=payload, token=token_hex)]
client.send_notification_batch(notifications=notifications, topic=topic)

# To use token based authentication
from apns2.credentials import TokenCredentials

auth_key_path = 'path/to/auth_key'
auth_key_id = 'app_auth_key_id'
team_id = 'app_team_id'
token_credentials = TokenCredentials(auth_key_path=auth_key_path, auth_key_id=auth_key_id, team_id=team_id)
client = APNsClient(credentials=token_credentials, use_sandbox=False)
client.send_notification_batch(notifications=notifications, topic=topic)
```

## Further Info

[iOS Reference Library: Local and Push Notification Programming Guide][a1]

## Contributing

To develop PyAPNs2, check out the code and install dependencies. It's recommended to use a virtualenv to isolate dependencies:
```shell
# Clone the source code.
git clone https://github.com/Pr0Ger/PyAPNs2.git
cd PyAPNs2
# Create a virtualenv and install dependencies.
virtualenv venv
. venv/bin/activate
pip install -e .[tests]
```

To run the tests:
```shell
pytest
```

You can use `tox` for running tests with all supported Python versions:
```shell
pyenv install 3.5.6; pyenv install 3.6.7; pyenv install 3.7.1; pyenv install 3.8.0
pyenv local 3.8.0 3.7.1 3.6.7 3.5.6
pip install tox
tox
```

To run the linter:
```shell
pip install pylint
pylint --reports=n apns2 test
```

## License

PyAPNs2 is distributed under the terms of the MIT license.

See [LICENSE](LICENSE) file for the complete license details.

[a1]:https://developer.apple.com/documentation/usernotifications?language=objc
