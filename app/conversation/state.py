"""State - abstract base for every conversation state (Dev 3's design)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.conversation.context import Context
    from app.conversation.transition import Transition


class State(ABC):
    @abstractmethod
    def handle(self, context: "Context", message: str) -> "Transition":
        """Handle one message in this state; return the Transition to apply."""
        ...

    @property
    def name(self) -> str:
        return type(self).__name__
