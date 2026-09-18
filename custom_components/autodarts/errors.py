"""Shared exceptions for local and cloud Autodarts APIs."""


class AutodartsApiError(Exception):
    """Base exception for Autodarts API errors."""


class AutodartsConnectionError(AutodartsApiError):
    """Transport, service or malformed response error."""


class AutodartsAuthError(AutodartsApiError):
    """Authentication failed with a machine-readable OAuth error."""

    def __init__(self, code: str = "invalid_token") -> None:
        self.code = code
        super().__init__(code)
