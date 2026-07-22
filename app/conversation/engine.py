"""StateMachineEngine - coordinates one turn (Dev 3's design).

Asks the current state to handle the message, applies the Transition to the
Context, and returns the reply text. No business logic lives here.
"""
from __future__ import annotations

from app.conversation.context import Context


class StateMachineEngine:
    def __init__(self, context: Context) -> None:
        self.context = context

    def process_message(self, message: str) -> str:
        current_state = self.context.current_state
        transition = current_state.handle(self.context, message)

        if transition.next_state is not None:
            self.context.current_state = transition.next_state

        for key, value in transition.context_updates.items():
            setattr(self.context, key, value)

        return transition.reply_text
