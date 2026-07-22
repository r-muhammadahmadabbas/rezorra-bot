"""Transition - the result of a State.handle() call (Dev 3's design)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from app.conversation.state import State


@dataclass
class Transition:
    next_state: "State | None"           # None = stay in the same state
    reply_text: str
    context_updates: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
