from demo.core.error.exception_handler_factory import http_exception_handler_factory
from demo.iam.domain.error import AccessDeniedException, AuthenticationException


def exception_handler_register_to(app):

    app.add_exception_handler(
        AuthenticationException,
        http_exception_handler_factory(401),
    )

    app.add_exception_handler(
        AccessDeniedException,
        http_exception_handler_factory(403),
    )


def authentication_exception_callback(exc: Exception | None = None):
    if exc:
        raise AuthenticationException() from exc
    raise AuthenticationException()


def access_denied_exception_callback(exc: Exception | None = None):
    if exc:
        raise AccessDeniedException() from exc
    raise AccessDeniedException()
