class APNsException(Exception):
    pass


class InternalException(APNsException):
    """This exception should not be raised. If it is, please report this as a bug."""
    pass


class BadPayloadException(APNsException):
    """Something bad with the payload."""
    pass


class PayloadEmpty(BadPayloadException):
    """The message payload was empty."""
    pass


class PayloadTooLarge(BadPayloadException):
    """The message payload was too large. The maximum payload size is 4096 bytes."""
    pass


class BadTopic(BadPayloadException):
    """The apns-topic was invalid."""
    pass


class TopicDisallowed(BadPayloadException):
    """Pushing to this topic is not allowed."""
    pass


class BadMessageId(InternalException):
    """The apns-id value is bad."""
    pass


class BadExpirationDate(BadPayloadException):
    """The apns-expiration value is bad."""
    pass


class BadPriority(InternalException):
    """The apns-priority value is bad."""
    pass


class MissingDeviceToken(APNsException):
    """The device token is not specified in the request :path.
    Verify that the :path header contains the device token."""
    pass


class BadDeviceToken(APNsException):
    """The specified device token was bad.
    Verify that the request contains a valid token and that the token matches the environment."""
    pass


class DeviceTokenNotForTopic(APNsException):
    """The device token does not match the specified topic."""


class Unregistered(APNsException):
    """The device token is inactive for the specified topic."""


class DuplicateHeaders(InternalException):
    """One or more headers were repeated."""
    pass


class BadCertificateEnvironment(APNsException):
    """The client certificate was for the wrong environment."""
    pass


class BadCertificate(APNsException):
    """The certificate was bad."""
    pass


class Forbidden(APNsException):
    """The specified action is not allowed."""
    pass


class BadPath(APNsException):
    """The request contained a bad :path value."""
    pass


class MethodNotAllowed(InternalException):
    """The specified :method was not POST."""
    pass


class TooManyRequests(APNsException):
    """Too many requests were made consecutively to the same device token."""
    pass


class IdleTimeout(APNsException):
    """Idle time out."""
    pass


class Shutdown(APNsException):
    """The server is shutting down."""
    pass


class InternalServerError(APNsException):
    """An internal server error occurred."""
    pass


class ServiceUnavailable(APNsException):
    """The service is unavailable."""
    pass


class MissingTopic(BadPayloadException):
    """The apns-topic header of the request was not specified and was required.
    The apns-topic header is mandatory when the client is connected using a certificate
    that supports multiple topics."""
    pass


def exception_class_for_reason(reason):
    return {
        'PayloadEmpty': PayloadEmpty,
        'PayloadTooLarge': PayloadTooLarge,
        'BadTopic': BadTopic,
        'TopicDisallowed': TopicDisallowed,
        'BadMessageId': BadMessageId,
        'BadExpirationDate': BadExpirationDate,
        'BadPriority': BadPriority,
        'MissingDeviceToken': MissingDeviceToken,
        'BadDeviceToken': BadDeviceToken,
        'DeviceTokenNotForTopic': DeviceTokenNotForTopic,
        'Unregistered': Unregistered,
        'DuplicateHeaders': DuplicateHeaders,
        'BadCertificateEnvironment': BadCertificateEnvironment,
        'BadCertificate': BadCertificate,
        'Forbidden': Forbidden,
        'BadPath': BadPath,
        'MethodNotAllowed': MethodNotAllowed,
        'TooManyRequests': TooManyRequests,
        'IdleTimeout': IdleTimeout,
        'Shutdown': Shutdown,
        'InternalServerError': InternalServerError,
        'ServiceUnavailable': ServiceUnavailable,
        'MissingTopic': MissingTopic,
    }[reason]
