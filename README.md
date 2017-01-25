# PyAPNs2

[![PyPI version](https://img.shields.io/pypi/v/apns2.svg)](https://pypi.python.org/pypi/apns2)
[![PyPI version](https://img.shields.io/pypi/pyversions/apns2.svg)](https://pypi.python.org/pypi/apns2)
[![Build Status](https://img.shields.io/travis/Pr0Ger/PyAPNs2.svg)](https://travis-ci.org/Pr0Ger/PyAPNs2)
[![Code Climate](https://img.shields.io/codeclimate/github/Pr0Ger/PyAPNs2.svg)](https://codeclimate.com/github/Pr0Ger/PyAPNs2)

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

## Contributing

To develop PyAPNs2, check out the code and install dependencies. It's recommended to use a virtualenv to isolate dependencies:
```shell
# Clone the source code.
git clone https://github.com/Pr0ger/PyAPNs2.git
cd PyAPNs2
# Create a virtualenv and install dependencies.
virtualenv venv
. venv/bin/activate
pip install -e .
```

To run the tests:
```shell
pip install -r requirements-dev.txt
python -m unittest discover test
```

To run the linter:
```shell
pip install pylint
pylint --reports=n apns2 test
```

## License

PyAPNs2 is distributed under the terms of the MIT license.

See [LICENSE](LICENSE) file for the complete license details.

[a1]:https://developer.apple.com/library/content/documentation/NetworkingInternet/Conceptual/RemoteNotificationsPG/
