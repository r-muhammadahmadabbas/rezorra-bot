"""Context - one user's conversation memory (Dev 3's design + stuck counter)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from app.conversation.state import State


@dataclass
class Context:
    current_state: "State"
    customer_name: str | None = None
    customer_phone: str | None = None
    language: str = "English"
    selected_category: str | None = None
    selected_product: str | None = None
    # How many messages in a row we failed to understand. When this crosses the
    # threshold the bot hands off to a human. Reset to 0 on any understood input.
    unrecognized_count: int = 0
    session_data: dict[str, Any] = field(default_factory=dict)
