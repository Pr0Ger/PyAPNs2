from typing import Type, Optional


class APNsException(Exception):
    pass


class ConnectionFailed(APNsException):
    """There was an error connecting to APNs."""


class InternalException(APNsException):
    """This exception should not be raised. If it is, please report this as a bug."""
    pass


class BadPayloadException(APNsException):
    """Something bad with the payload."""
    pass


class BadCollapseId(BadPayloadException):
    """The collapse identifier exceeds the maximum allowed size"""
    pass


class BadDeviceToken(APNsException):
    """The specified device token was bad.
    Verify that the request contains a valid token and that the token matches the environment."""
    pass


class BadExpirationDate(BadPayloadException):
    """The apns-expiration value is bad."""
    pass


class BadMessageId(InternalException):
    """The apns-id value is bad."""
    pass


class BadPriority(InternalException):
    """The apns-priority value is bad."""
    pass


class BadTopic(BadPayloadException):
    """The apns-topic was invalid."""
    pass


class DeviceTokenNotForTopic(APNsException):
    """The device token does not match the specified topic."""


class DuplicateHeaders(InternalException):
    """One or more headers were repeated."""
    pass


class IdleTimeout(APNsException):
    """Idle time out."""
    pass


class MissingDeviceToken(APNsException):
    """The device token is not specified in the request :path.
    Verify that the :path header contains the device token."""
    pass


class MissingTopic(BadPayloadException):
    """The apns-topic header of the request was not specified and was required.
    The apns-topic header is mandatory when the client is connected using a certificate
    that supports multiple topics."""
    pass


class PayloadEmpty(BadPayloadException):
    """The message payload was empty."""
    pass


class TopicDisallowed(BadPayloadException):
    """Pushing to this topic is not allowed."""
    pass


class BadCertificate(APNsException):
    """The certificate was bad."""
    pass


class BadCertificateEnvironment(APNsException):
    """The client certificate was for the wrong environment."""
    pass


class ExpiredProviderToken(APNsException):
    """The provider token is stale and a new token should be generated."""
    pass


class Forbidden(APNsException):
    """The specified action is not allowed."""
    pass


class InvalidProviderToken(APNsException):
    """The provider token is not valid or the token signature could not be verified."""
    pass


class MissingProviderToken(APNsException):
    """No provider certificate was used to connect to APNs and Authorization header was missing or no provider token
    was specified. """
    pass


class BadPath(APNsException):
    """The request contained a bad :path value."""
    pass


class MethodNotAllowed(InternalException):
    """The specified :method was not POST."""
    pass


class Unregistered(APNsException):
    """The device token is inactive for the specified topic."""

    def __init__(self, timestamp: Optional[str] = None) -> None:
        super(Unregistered, self).__init__()

        self.timestamp = timestamp


class PayloadTooLarge(BadPayloadException):
    """The message payload was too large. The maximum payload size is 4096 bytes."""
    pass


class TooManyProviderTokenUpdates(APNsException):
    """The provider token is being updated too often."""
    pass


class TooManyRequests(APNsException):
    """Too many requests were made consecutively to the same device token."""
    pass


class InternalServerError(APNsException):
    """An internal server error occurred."""
    pass


class ServiceUnavailable(APNsException):
    """The service is unavailable."""
    pass


class Shutdown(APNsException):
    """The server is shutting down."""
    pass


def exception_class_for_reason(reason: str) -> Type[APNsException]:
    return {
        'BadCollapseId': BadCollapseId,
        'BadDeviceToken': BadDeviceToken,
        'BadExpirationDate': BadExpirationDate,
        'BadMessageId': BadMessageId,
        'BadPriority': BadPriority,
        'BadTopic': BadTopic,
        'DeviceTokenNotForTopic': DeviceTokenNotForTopic,
        'DuplicateHeaders': DuplicateHeaders,
        'IdleTimeout': IdleTimeout,
        'MissingDeviceToken': MissingDeviceToken,
        'MissingTopic': MissingTopic,
        'PayloadEmpty': PayloadEmpty,
        'TopicDisallowed': TopicDisallowed,
        'BadCertificate': BadCertificate,
        'BadCertificateEnvironment': BadCertificateEnvironment,
        'ExpiredProviderToken': ExpiredProviderToken,
        'Forbidden': Forbidden,
        'InvalidProviderToken': InvalidProviderToken,
        'MissingProviderToken': MissingProviderToken,
        'BadPath': BadPath,
        'MethodNotAllowed': MethodNotAllowed,
        'Unregistered': Unregistered,
        'PayloadTooLarge': PayloadTooLarge,
        'TooManyProviderTokenUpdates': TooManyProviderTokenUpdates,
        'TooManyRequests': TooManyRequests,
        'InternalServerError': InternalServerError,
        'ServiceUnavailable': ServiceUnavailable,
        'Shutdown': Shutdown,
    }[reason]
