"""HandoffState - a human is handling the chat; the bot is muted.

Reached by an explicit agent request, "place an order", or the stuck signal. To
avoid a dead-end in the prototype (there is no live agent answering yet), the
user can get the bot back easily: any menu number or greeting resumes it and
acts on the selection. Free text stays muted (that's what a human would answer).
"""
from __future__ import annotations

from app import data
from app.conversation.state import State
from app.conversation.transition import Transition

RESUME = {"menu", "main menu", "resume", "bot", "start", "back", "0",
          "hi", "hello", "salam", "asalam o alaikum"}


class HandoffState(State):
    def handle(self, context, message: str) -> Transition:
        text = str(message).strip().lower()
        from app.conversation.states.main_menu import MainMenuState, _route_intent

        # A greeting / "menu" brings the bot back and shows the menu.
        if text in RESUME:
            return Transition(MainMenuState(), data.format_main_menu("Bot re-enabled."),
                              {"unrecognized_count": 0})

        # A menu number brings the bot back AND acts on that choice.
        item = data.menu_item_for(text)
        if item:
            transition = _route_intent(item.intent)
            if transition.next_state is None:      # a "stay in menu" answer
                transition.next_state = MainMenuState()
            return transition

        # Free text: stay muted, a human would reply here.
        return Transition(
            None,
            "You're connected to our team - someone will reply here shortly. "
            "(Type MENU to talk to the bot again.)",
        )
