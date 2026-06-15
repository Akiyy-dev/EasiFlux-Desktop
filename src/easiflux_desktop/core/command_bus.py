"""Command bus for UI-initiated operations."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, TypeVar

from easiflux_desktop.core.errors import DesktopError
from easiflux_desktop.core.event_bus import EventBus

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class CommandResult:
    success: bool
    data: Any = None
    error: DesktopError | None = None


class CommandBus:
    """Dispatches async commands with unified error handling."""

    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus
        self._handlers: dict[type, Callable[..., Awaitable[Any]]] = {}

    def register(self, command_type: type, handler: Callable[..., Awaitable[Any]]) -> None:
        self._handlers[command_type] = handler

    async def execute(self, command: Any) -> CommandResult:
        handler = self._handlers.get(type(command))
        if handler is None:
            error = DesktopError(f"No handler registered for {type(command).__name__}")
            self._event_bus.publish("error.occurred", error)
            return CommandResult(success=False, error=error)

        try:
            data = await handler(command)
            return CommandResult(success=True, data=data)
        except DesktopError as exc:
            logger.warning("Command failed: %s", exc)
            self._event_bus.publish("error.occurred", exc)
            return CommandResult(success=False, error=exc)
        except Exception as exc:
            logger.exception("Unexpected command error")
            error = DesktopError(str(exc), cause=exc)
            self._event_bus.publish("error.occurred", error)
            return CommandResult(success=False, error=error)

    def execute_background(self, command: Any, on_complete: Callable[[CommandResult], None] | None = None) -> None:
        async def _run() -> None:
            result = await self.execute(command)
            if on_complete:
                on_complete(result)

        asyncio.create_task(_run())
