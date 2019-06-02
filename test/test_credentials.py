# This only tests the TokenCredentials test case, since the
# CertificateCredentials would be mocked out anyway.
# Namely:
# - timing out of the token
# - creating multiple tokens for different topics

import pytest
from freezegun import freeze_time

from apns2.credentials import TokenCredentials

TOPIC = 'com.example.first_app'


@pytest.fixture
def token_credentials():
    return TokenCredentials('test/eckey.pem', '1QBCDJ9RST', '3Z24IP123A')


def test_token_expiration(token_credentials):
    # As long as the token lifetime hasn't elapsed, this should work. To
    # be really careful, we should check how much time has elapsed to
    # know if it fail. But, either way, we'd have to come up with a good
    # lifetime for future tests...

    with freeze_time('2012-01-14'):
        expiring_header = token_credentials.get_authorization_header(TOPIC)

    new_header = token_credentials.get_authorization_header(TOPIC)
    assert expiring_header != new_header
