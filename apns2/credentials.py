import time
from typing import Optional, Tuple, TYPE_CHECKING

import jwt

from hyper import HTTP20Connection  # type: ignore
from hyper.tls import init_context  # type: ignore

if TYPE_CHECKING:
    from hyper.ssl_compat import SSLContext  # type: ignore

DEFAULT_TOKEN_LIFETIME = 2700
DEFAULT_TOKEN_ENCRYPTION_ALGORITHM = 'ES256'


# Abstract Base class. This should not be instantiated directly.
class Credentials(object):
    def __init__(self, ssl_context: 'Optional[SSLContext]' = None) -> None:
        super().__init__()
        self.__ssl_context = ssl_context

    # Creates a connection with the credentials, if available or necessary.
    def create_connection(self, server: str, port: int, proto: Optional[str], proxy_host: Optional[str] = None,
                          proxy_port: Optional[int] = None) -> HTTP20Connection:
        # self.__ssl_context may be none, and that's fine.
        return HTTP20Connection(server, port, ssl_context=self.__ssl_context, force_proto=proto or 'h2',
                                secure=True, proxy_host=proxy_host, proxy_port=proxy_port)

    def get_authorization_header(self, topic: Optional[str]) -> Optional[str]:
        return None


# Credentials subclass for certificate authentication
class CertificateCredentials(Credentials):
    def __init__(self, cert_file: Optional[str] = None, password: Optional[str] = None,
                 cert_chain: Optional[str] = None) -> None:
        ssl_context = init_context(cert=cert_file, cert_password=password)
        if cert_chain:
            ssl_context.load_cert_chain(cert_chain)
        super(CertificateCredentials, self).__init__(ssl_context)


# Credentials subclass for JWT token based authentication
class TokenCredentials(Credentials):
    def __init__(self, auth_key_path: str, auth_key_id: str, team_id: str,
                 encryption_algorithm: str = DEFAULT_TOKEN_ENCRYPTION_ALGORITHM,
                 token_lifetime: int = DEFAULT_TOKEN_LIFETIME) -> None:
        self.__auth_key = self._get_signing_key(auth_key_path)
        self.__auth_key_id = auth_key_id
        self.__team_id = team_id
        self.__encryption_algorithm = encryption_algorithm
        self.__token_lifetime = token_lifetime

        self.__jwt_token = None  # type: Optional[Tuple[float, str]]

        # Use the default constructor because we don't have an SSL context
        super(TokenCredentials, self).__init__()

    def get_authorization_header(self, topic: Optional[str]) -> str:
        token = self._get_or_create_topic_token()
        return 'bearer %s' % token

    def _is_expired_token(self, issue_date: float) -> bool:
        return time.time() > issue_date + self.__token_lifetime

    @staticmethod
    def _get_signing_key(key_path: str) -> str:
        secret = ''
        if key_path:
            with open(key_path) as f:
                secret = f.read()
        return secret

    def _get_or_create_topic_token(self) -> str:
        # dict of topic to issue date and JWT token
        token_pair = self.__jwt_token
        if token_pair is None or self._is_expired_token(token_pair[0]):
            # Create a new token
            issued_at = time.time()
            token_dict = {
                'iss': self.__team_id,
                'iat': issued_at,
            }
            headers = {
                'alg': self.__encryption_algorithm,
                'kid': self.__auth_key_id,
            }
            jwt_token = jwt.encode(token_dict, self.__auth_key,
                                   algorithm=self.__encryption_algorithm,
                                   headers=headers).decode('ascii')

            # Cache JWT token for later use. One JWT token per connection.
            # https://developer.apple.com/documentation/usernotifications/setting_up_a_remote_notification_server/establishing_a_token-based_connection_to_apns
            self.__jwt_token = (issued_at, jwt_token)
            return jwt_token
        else:
            return token_pair[1]
