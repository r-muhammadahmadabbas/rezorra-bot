"""MainMenuState - routes the numbered menu and free-text questions.

Content (prices, sizes, stock, delivery, FAQ) comes from `app.data`, never
hardcoded here. Unrecognised input increments the stuck counter and, past the
threshold, hands off to a human.
"""
from __future__ import annotations

from app import data
from app.conversation.state import State
from app.conversation.states import STUCK_THRESHOLD
from app.conversation.transition import Transition

RESHOW = {"menu", "main menu", "hi", "hello", "start", "0", "salam", "asalam o alaikum"}


class MainMenuState(State):
    def handle(self, context, message: str) -> Transition:
        text = str(message).strip().lower()

        # Re-show the menu on greetings / "menu".
        if text in RESHOW:
            return Transition(None, data.format_main_menu(), {"unrecognized_count": 0})

        # Numbered options.
        if text == "1":
            return Transition(None, data.format_prices(), {"unrecognized_count": 0})
        if text == "2":
            return Transition(None, data.format_sizes(), {"unrecognized_count": 0})
        if text == "3":
            return Transition(None, data.format_stock(), {"unrecognized_count": 0})
        if text == "4":
            return Transition(None, data.delivery_answer() + "\n\nType MENU for the options.",
                              {"unrecognized_count": 0})
        if text == "5":
            from app.conversation.states.handoff import HandoffState
            return Transition(
                HandoffState(),
                "Great! To place your order our team will take your details here. "
                "Connecting you to a team member now.",
                {"unrecognized_count": 0},
            )
        if text == "6":
            from app.conversation.states.faq import FAQState
            return Transition(
                FAQState(),
                "Sure - type your question. For example: \"delivery charges\", \"COD\", "
                "\"return policy\" or \"where are you located\".",
                {"unrecognized_count": 0},
            )
        if text == "7":
            from app.conversation.states.handoff import HandoffState
            return Transition(HandoffState(), "Connecting you to a team member - "
                              "they will reply here shortly.", {"unrecognized_count": 0})

        # Not a menu number - maybe they typed a question directly.
        faq = data.match_faq(text)
        if faq:
            return Transition(None, faq.answer + "\n\nType MENU for more options.",
                              {"unrecognized_count": 0})

        # Unrecognised - count it, and hand off if they seem stuck.
        return _stuck_or_retry(context, "Sorry, I didn't get that.")


def _stuck_or_retry(context, prefix: str) -> Transition:
    count = context.unrecognized_count + 1
    if count >= STUCK_THRESHOLD:
        from app.conversation.states.handoff import HandoffState
        return Transition(
            HandoffState(),
            "It looks like I'm having trouble helping. Let me connect you to a "
            "team member - they'll reply here shortly.",
            {"unrecognized_count": 0},
        )
    return Transition(None, f"{prefix}\n\n" + data.format_main_menu(),
                      {"unrecognized_count": count})
