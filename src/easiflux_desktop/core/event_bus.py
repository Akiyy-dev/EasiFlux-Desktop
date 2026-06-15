"""Application-wide event bus."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, Signal


class EventBus(QObject):
    """Pub/sub bus bridging async producers and Qt UI consumers."""

    event_emitted = Signal(str, object)

    def __init__(self) -> None:
        super().__init__()
        self._subscribers: dict[str, list[Callable[[Any], None]]] = defaultdict(list)
        self._sticky: dict[str, Any] = {}
        self.event_emitted.connect(self._dispatch_signal)

    def subscribe(self, event: str, handler: Callable[[Any], None]) -> None:
        self._subscribers[event].append(handler)
        if event in self._sticky:
            handler(self._sticky[event])

    def unsubscribe(self, event: str, handler: Callable[[Any], None]) -> None:
        handlers = self._subscribers.get(event, [])
        if handler in handlers:
            handlers.remove(handler)

    def publish(self, event: str, payload: Any = None, *, sticky: bool = False) -> None:
        if sticky:
            self._sticky[event] = payload
        self.event_emitted.emit(event, payload)

    def get_sticky(self, event: str) -> Any | None:
        return self._sticky.get(event)

    def clear_sticky(self, event: str) -> None:
        self._sticky.pop(event, None)

    def _dispatch_signal(self, event: str, payload: object) -> None:
        for handler in list(self._subscribers.get(event, [])):
            handler(payload)
