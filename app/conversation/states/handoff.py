"""HandoffState - the bot is muted; a human is handling the chat.

Reached by an explicit agent request (from any state, via the bridge), by
'place an order', or by the stuck signal. The user can type MENU to hand control
back to the bot. In the full product this is where Dev 4's agent dashboard picks
the conversation up.
"""
from __future__ import annotations

from app import data
from app.conversation.state import State
from app.conversation.transition import Transition

RESUME = {"menu", "main menu", "resume", "bot", "start", "0"}


class HandoffState(State):
    def handle(self, context, message: str) -> Transition:
        text = str(message).strip().lower()

        if text in RESUME:
            from app.conversation.states.main_menu import MainMenuState
            return Transition(
                MainMenuState(),
                data.format_main_menu("Bot re-enabled."),
                {"unrecognized_count": 0},
            )

        # Muted: acknowledge once, don't run bot logic.
        return Transition(
            None,
            "You're connected to our team - someone will reply here shortly. "
            "(Type MENU to talk to the bot again.)",
        )
