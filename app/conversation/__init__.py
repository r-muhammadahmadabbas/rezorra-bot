"""Conversation engine (Dev 3's state machine, integrated).

Ported from `rezoraa-whatsup-bot/state_machine` + `states`, adapted to:
  - carry a per-user stuck counter (the handoff signal),
  - pull all product/FAQ content from `app.data` instead of hardcoding it.

Dev 1's connectivity layer drives this via `app.handlers_bot`.
"""
