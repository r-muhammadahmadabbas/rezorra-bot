"""MainMenuState - routes the numbered menu (by intent) and free-text questions.

Menu content comes from app.data (DB-backed). Routing is by the option's
*intent*, so it works whether the DB menu uses numbers or words. Unrecognised
input increments the stuck counter and, past the threshold, hands off.
"""
from __future__ import annotations

from app import data
from app.conversation.state import State
from app.conversation.states import STUCK_THRESHOLD
from app.conversation.transition import Transition

RESHOW = {"menu", "main menu", "hi", "hello", "start", "0", "salam", "asalam o alaikum"}
RESET = {"unrecognized_count": 0}


class MainMenuState(State):
    def handle(self, context, message: str) -> Transition:
        text = str(message).strip().lower()

        # Empty/whitespace or a greeting: just (re)show the menu, don't count it
        # against the stuck-handoff threshold.
        if not text or text in RESHOW:
            return Transition(None, data.format_main_menu(), dict(RESET))

        # Numbered menu selection -> route by the option's intent.
        item = data.menu_item_for(text)
        if item:
            return _route_intent(item.intent)

        # Not a menu number - maybe a direct question.
        faq = data.match_faq(text)
        if faq:
            return Transition(None, faq.answer + "\n\nType MENU for more options.", dict(RESET))

        return _stuck_or_retry(context, "Sorry, I didn't get that.")


def _route_intent(intent: str) -> Transition:
    if intent == "price":
        return Transition(None, data.format_prices(), dict(RESET))
    if intent == "sizes":
        return Transition(None, data.format_sizes(), dict(RESET))
    if intent == "stock":
        return Transition(None, data.format_stock(), dict(RESET))
    if intent == "delivery":
        return Transition(None, data.delivery_answer() + "\n\nType MENU for the options.", dict(RESET))
    if intent == "recommendation":
        return Transition(None, data.format_recommendation(), dict(RESET))
    if intent == "faq":
        from app.conversation.states.faq import FAQState
        return Transition(FAQState(),
                          "Sure - type your question. For example: \"delivery charges\", "
                          "\"COD\", \"return policy\" or \"where are you located\".", dict(RESET))
    if intent == "order":
        from app.conversation.states.handoff import HandoffState
        return Transition(HandoffState(),
                          "Great! To place your order our team will take your details here. "
                          "Connecting you to a team member now.", dict(RESET))
    if intent == "agent":
        from app.conversation.states.handoff import HandoffState
        return Transition(HandoffState(),
                          "Connecting you to a team member - they will reply here shortly.", dict(RESET))
    # Unknown intent - just re-show the menu.
    return Transition(None, data.format_main_menu(), dict(RESET))


def _stuck_or_retry(context, prefix: str) -> Transition:
    count = context.unrecognized_count + 1
    if count >= STUCK_THRESHOLD:
        from app.conversation.states.handoff import HandoffState
        return Transition(
            HandoffState(),
            "It looks like I'm having trouble helping. Let me connect you to a "
            "team member - they'll reply here shortly.",
            dict(RESET),
        )
    return Transition(None, f"{prefix}\n\n" + data.format_main_menu(),
                      {"unrecognized_count": count})
