"""Supabase / PostgreSQL access (Dev 2's schema + Dev 4's services).

Only reference-data READS are on the bot's hot path this week, and those are
served from an in-memory catalog (see app/catalog.py) that is loaded from here at
startup. This keeps Dev 3's synchronous state machine unchanged.
"""
