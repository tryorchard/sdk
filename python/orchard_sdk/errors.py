"""Exceptions raised by the Orchard SDK."""
from __future__ import annotations


class OrchardError(Exception):
    """Base class for every error the SDK raises."""


class ApiError(OrchardError):
    """A non-2xx REST response.

    Attributes:
        status: The HTTP status code.
        detail: The server's ``detail`` message (or a best-effort body excerpt).
    """

    def __init__(self, status: int, detail: str):
        self.status = status
        self.detail = detail
        super().__init__(self.user_message)

    @property
    def user_message(self) -> str:
        """A human-friendly, actionable message for the terminal/logs."""
        if self.status == 401:
            return "the API key is invalid or expired (check ORCHARD_API_KEY)"
        if self.status == 403:
            return self.detail or "forbidden"
        if self.status == 404:
            return self.detail or "no such sandbox, or this key may not reach it"
        return self.detail or f"request failed ({self.status})"


class SelectorError(OrchardError):
    """A sandbox selector matched zero or more than one sandbox."""


class ChannelClosedError(OrchardError):
    """A WebSocket channel closed with an error code.

    Attributes:
        code: The WebSocket close code (4401 unauth, 4403 forbidden,
            4404 not found, 4502 upstream agent unreachable).
        reason: The server's close reason, if any.
    """

    def __init__(self, code: int, reason: str = ""):
        self.code = code
        self.reason = reason
        super().__init__(f"channel closed ({code})" + (f": {reason}" if reason else ""))
