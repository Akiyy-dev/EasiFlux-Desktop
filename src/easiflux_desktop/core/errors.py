"""Desktop exception hierarchy."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ErrorCategory(str, Enum):
    CONNECTION = "connection"
    AUTHENTICATION = "authentication"
    TRADING = "trading"
    VALIDATION = "validation"
    CONFIGURATION = "configuration"
    RISK = "risk"
    STRATEGY = "strategy"
    UNKNOWN = "unknown"


@dataclass
class DesktopError(Exception):
    message: str
    category: ErrorCategory = ErrorCategory.UNKNOWN
    cause: Exception | None = None
    recoverable: bool = True

    def __str__(self) -> str:
        return self.message

    @property
    def user_message(self) -> str:
        return self.message


class ConnectionError(DesktopError):
    def __init__(self, message: str, *, cause: Exception | None = None) -> None:
        super().__init__(message, category=ErrorCategory.CONNECTION, cause=cause)


class AuthenticationError(DesktopError):
    def __init__(self, message: str, *, cause: Exception | None = None) -> None:
        super().__init__(
            message,
            category=ErrorCategory.AUTHENTICATION,
            cause=cause,
            recoverable=True,
        )


class TradingError(DesktopError):
    def __init__(self, message: str, *, cause: Exception | None = None) -> None:
        super().__init__(message, category=ErrorCategory.TRADING, cause=cause)


class ValidationError(DesktopError):
    def __init__(self, message: str) -> None:
        super().__init__(message, category=ErrorCategory.VALIDATION, recoverable=True)


class RiskError(DesktopError):
    def __init__(self, message: str) -> None:
        super().__init__(message, category=ErrorCategory.RISK, recoverable=True)


class ConfigurationError(DesktopError):
    def __init__(self, message: str, *, cause: Exception | None = None) -> None:
        super().__init__(message, category=ErrorCategory.CONFIGURATION, cause=cause)
