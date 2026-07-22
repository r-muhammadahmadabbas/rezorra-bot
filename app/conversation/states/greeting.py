"""GreetingState - the first turn. Welcomes the user and shows the menu."""
from __future__ import annotations

from app import data
from app.conversation.state import State
from app.conversation.transition import Transition


class GreetingState(State):
    def handle(self, context, message: str) -> Transition:
        from app.conversation.states.main_menu import MainMenuState

        name = f" {context.customer_name}" if context.customer_name else ""
        header = f"Welcome to Rezorra{name}! Your online clothing store."
        return Transition(
            next_state=MainMenuState(),
            reply_text=data.format_main_menu(header),
        )
