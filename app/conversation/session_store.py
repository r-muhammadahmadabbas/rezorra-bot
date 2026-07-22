"""Per-user session store.

Keeps one Context per WhatsApp number so the bot remembers where each user is
mid-conversation. In-memory is fine for the prototype (the PM said so); this is
the seam where Dev 4's persisted `BotSession` (Supabase) plugs in later.
"""
from __future__ import annotations

from app.conversation.context import Context
from app.conversation.states.greeting import GreetingState

_sessions: dict[str, Context] = {}


def get_or_create(user_id: str) -> Context:
    ctx = _sessions.get(user_id)
    if ctx is None:
        ctx = Context(current_state=GreetingState(), customer_phone=user_id)
        _sessions[user_id] = ctx
    return ctx


def reset(user_id: str) -> None:
    _sessions.pop(user_id, None)
