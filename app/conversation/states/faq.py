"""FAQState - free-text question answering, backed by `app.data`.

Staying in this state between questions is what proves the bot 'remembers' where
the user is: they can ask several questions in a row without resetting to the
welcome. 'menu' returns to the main menu; repeated misses hand off.
"""
from __future__ import annotations

from app import data
from app.conversation.state import State
from app.conversation.states import STUCK_THRESHOLD
from app.conversation.transition import Transition


class FAQState(State):
    def handle(self, context, message: str) -> Transition:
        text = str(message).strip().lower()

        if text in {"menu", "main menu", "back", "0"}:
            from app.conversation.states.main_menu import MainMenuState
            return Transition(MainMenuState(), data.format_main_menu("Back to the menu."),
                              {"unrecognized_count": 0})

        faq = data.match_faq(text)
        if faq:
            return Transition(
                None,
                faq.answer + "\n\nAsk another question, or type MENU for the options.",
                {"unrecognized_count": 0},
            )

        count = context.unrecognized_count + 1
        if count >= STUCK_THRESHOLD:
            from app.conversation.states.handoff import HandoffState
            return Transition(
                HandoffState(),
                "I couldn't find an answer to that. Let me connect you to a team "
                "member who can help.",
                {"unrecognized_count": 0},
            )
        return Transition(
            None,
            "I couldn't find that in our FAQs. Try rephrasing (e.g. \"delivery\", "
            "\"COD\", \"returns\"), or type MENU.",
            {"unrecognized_count": count},
        )
