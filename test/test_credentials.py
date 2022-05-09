# This only tests the TokenCredentials test case, since the
# CertificateCredentials would be mocked out anyway.
# Namely:
# - timing out of the token
# - creating multiple tokens for different topics

from base64 import b64encode
import pytest
from freezegun import freeze_time

from apns2.credentials import TokenCredentials

TOPIC = 'com.example.first_app'


@pytest.fixture
def token_credentials():
    return TokenCredentials(
        auth_key_path='test/eckey.pem',
        auth_key_id='1QBCDJ9RST',
        team_id='3Z24IP123A',
        token_lifetime=30,  # seconds
    )

def test_auth_key_base64():
    with open('test/eckey.pem', 'rb') as f:
        auth_key_base64 = b64encode(f.read()).decode()
    assert TokenCredentials._get_signing_key('test/eckey.pem') == TokenCredentials._decode_signing_key(auth_key_base64)

def test_token_expiration(token_credentials):
    with freeze_time('2012-01-14 12:00:00'):
        header1 = token_credentials.get_authorization_header(TOPIC)

    # 20 seconds later, before expiration, same JWT
    with freeze_time('2012-01-14 12:00:20'):
        header2 = token_credentials.get_authorization_header(TOPIC)
        assert header1 == header2

    # 35 seconds later, after expiration, new JWT
    with freeze_time('2012-01-14 12:00:40'):
        header3 = token_credentials.get_authorization_header(TOPIC)
        assert header3 != header1
