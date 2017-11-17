# This only tests the TokenCredentials test case, since the
# CertificateCredentials would be mocked out anyway.
# Namely:
# - timing out of the token
# - creating multiple tokens for different topics

from unittest import TestCase, main

from freezegun import freeze_time

import time

from apns2.credentials import TokenCredentials


class TokenCredentialsTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.key_path = 'test/eckey.pem'
        cls.team_id = '3Z24IP123A'
        cls.key_id = '1QBCDJ9RST'
        cls.topics = ('com.example.first_app', 'com.example.second_app',)
        cls.token_lifetime = 0.5

    def setUp(self):
        # Create an 'ephemeral' token so we can test token timeouts. We
        # want a timeout long enough to last the test, but we don't want to
        # slow down the tests too much either.
        self.normal_creds = TokenCredentials(self.key_path, self.key_id,
                                             self.team_id)
        self.lasting_header = self.normal_creds.get_authorization_header(
            self.topics[0])

        with freeze_time('2012-01-14'):
            self.expiring_creds = \
                TokenCredentials(self.key_path, self.key_id,
                                 self.team_id,
                                 token_lifetime=self.token_lifetime)
            self.expiring_header = self.expiring_creds.get_authorization_header(
                self.topics[0])

    def test_create_multiple_topics(self):
        h1 = self.normal_creds.get_authorization_header(self.topics[0])
        self.assertEqual(len(self.normal_creds.get_tokens()), 1)
        h2 = self.normal_creds.get_authorization_header(self.topics[1])
        self.assertNotEqual(h1, h2)
        self.assertEqual(len(self.normal_creds.get_tokens()), 2)

    def test_token_expiration(self):
        # As long as the token lifetime hasn't elapsed, this should work. To
        # be really careful, we should check how much time has elapsed to
        # know if it fail. But, either way, we'd have to come up with a good
        # lifetime for future tests...
        time.sleep(self.token_lifetime)
        h3 = self.expiring_creds.get_authorization_header(self.topics[0])
        self.assertNotEqual(self.expiring_header, h3)


if __name__ == '__main__':
    main()
