
from hyper import HTTP20Connection
from hyper.tls import init_context

import jwt

# For creating and comparing the time for the JWT token
import time


DEFAULT_TOKEN_LIFETIME = 3600
DEFAULT_TOKEN_ENCRYPTION_ALGORITHM = 'ES256'


# Abstract Base class. This should not be instantiated directly.
class Credentials(object):

    def __init__(self, ssl_context=None):
        self.__ssl_context = ssl_context

    # Creates a connection with the credentials, if available or necessary.
    def create_connection(self, server, port, proto):
        # self.__ssl_context may be none, and that's fine.
        return HTTP20Connection(server, port,
                                ssl_context=self.__ssl_context,
                                force_proto=proto or 'h2')

    def get_authorization_header(self, topic):
        return None


# Credentials subclass for certificate authentication
class CertificateCredentials(Credentials):
    def __init__(self, cert_file=None, password=None, cert_chain=None):
        ssl_context = init_context(cert=cert_file, cert_password=password)
        if cert_chain:
            ssl_context.load_cert_chain(cert_chain)
        super(CertificateCredentials, self).__init__(ssl_context)


# Credentials subclass for JWT token based authentication
class TokenCredentials(Credentials):
    def __init__(self, auth_key_path, auth_key_id, team_id,
                 encryption_algorithm=None, token_lifetime=None):
        self.__auth_key = self._get_signing_key(auth_key_path)
        self.__auth_key_id = auth_key_id
        self.__team_id = team_id
        self.__encryption_algorithm = DEFAULT_TOKEN_ENCRYPTION_ALGORITHM if \
            encryption_algorithm is None else \
            encryption_algorithm
        self.__token_lifetime = DEFAULT_TOKEN_LIFETIME if \
            token_lifetime is None else token_lifetime

        # Dictionary of {topic: (issue time, ascii decoded token)}
        self.__topicTokens = {}

        # Use the default constructor because we don't have an SSL context
        super(TokenCredentials, self).__init__()

    def get_tokens(self):
        return [val[1] for val in self.__topicTokens]

    def get_authorization_header(self, topic):
        token = self._get_or_create_topic_token(topic)
        return 'bearer %s' % token

    def _isExpiredToken(self, issueDate):
        now = time.time()
        return now < issueDate + DEFAULT_TOKEN_LIFETIME

    def _get_or_create_topic_token(self, topic):
        # dict of topic to issue date and JWT token
        tokenPair = self.__topicTokens.get(topic)
        if tokenPair is None or self._isExpiredToken(tokenPair[0]):
            # Create a new token
            issuedAt = time.time()
            tokenDict = {'iss': self.__team_id,
                         'iat': issuedAt
                         }
            headers = {'alg': self.__encryption_algorithm,
                       'kid': self.__auth_key_id,
                       }
            jwtToken = jwt.encode(tokenDict, self.__auth_key,
                                  algorithm=self.__encryption_algorithm,
                                  headers=headers).decode('ascii')

            self.__topicTokens[topic] = (issuedAt, jwtToken)
            return jwtToken
        else:
            return tokenPair[1]

    def _get_signing_key(self, key_path):
        secret = ''
        if key_path:
            with open(key_path) as f:
                secret = f.read()
        return secret
