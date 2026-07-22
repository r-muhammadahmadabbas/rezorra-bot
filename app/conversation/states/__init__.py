"""Conversation states (Dev 3's design + Dev 4's menu/FAQ/handoff content).

In scope this week: greeting, main menu, FAQ, human handoff. Out of scope
(order tracking, payments, courier) is intentionally not built.

STUCK_THRESHOLD is the "stuck" signal the PM asked for: after this many
unrecognised inputs in a row, the bot hands off to a human.
"""
STUCK_THRESHOLD = 2
