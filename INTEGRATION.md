# Rezorra — Integration (Week 1)

Three separate codebases merged into one working bot, in the layered architecture
we were assigned: **Dev 1 connectivity → Dev 3 state machine → Dev 2/4 data.**

## Where each person's work lives now

| Layer | Owner | Files | Source repo |
|---|---|---|---|
| WhatsApp connectivity (webhook, signature, dedupe, senders) | Dev 1 | `app/main.py`, `app/normalizer.py`, `app/schemas.py`, `app/dedupe.py`, `app/senders/`, `app/router.py` | `rezorra-bot` |
| State machine (engine, states, session) | Dev 3 | `app/conversation/` | `rezoraa-whatsup-bot` |
| Product / FAQ / menu data | Dev 2 + Dev 4 | `app/data.py` | `Rezorra_dev4-week1` (seed content) |
| The bridge that wires them | Dev 1 | `app/handlers_bot.py` | new |

## One message, end to end
```
WhatsApp → POST /webhook            (Dev 1: verify signature, dedupe, 200 fast)
         → normalize to IncomingMessage
         → handlers_bot.handle(msg, wa)
              → session_store: load this user's Context      (Dev 3 memory)
              → escalation? ("agent"/"human"/"numainda"…) → Handoff  (from any state)
              → StateMachineEngine.process_message(text)     (Dev 3 engine + states)
                   states read prices/sizes/stock/FAQ from   (Dev 2/4 data)
              → reply sent via wa.send_text                  (Dev 1 sender: mock or Cloud API)
```

## What was reconciled
- **Three webhooks → one.** Dev 4's `main.py` and its `whatsapp_client.py` were
  retired in favour of Dev 1's connectivity (it has signature verification + dedupe
  + mock/cloud modes, and is live-tested against Meta).
- **Two state machines → one.** Dev 4's string-state `bot_logic.py` was replaced by
  Dev 3's `State`/`Transition`/`Context` engine (the assigned owner of this layer).
  Dev 4's menu/FAQ/handoff *behaviour* was reused as the content of those states.
- **Data made local.** Dev 4's Supabase schema needs a live DB (and its `seed.py`
  didn't match its `models.py`). For a local prototype the same content lives in
  `app/data.py` as a plain repository. Function names mirror Dev 4's services
  (`match_faq`, `is_escalation`), so swapping in the real Supabase layer later is
  a drop-in — no state changes.

## Scope (per the PM)
- **Built:** welcome + menu, FAQ answering, product data (price/sizes/stock/delivery)
  from the data layer, human handoff (explicit request + "stuck" signal), per-user
  session memory.
- **Not built:** order tracking, payments, courier — intentionally out of scope.

## Run it
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# another terminal - test with NO Meta account:
python tools/send_fake_webhook.py text "hi"
python tools/send_fake_webhook.py text "1"
python tools/send_fake_webhook.py text "delivery charges kitne hain"
python tools/send_fake_webhook.py text "agent"
```
Replies print in the server terminal (mock mode). For real WhatsApp, set
`WHATSAPP_MODE=cloud` in `.env` — see README.

## Verified working
- greeting → menu → prices/sizes/stock/delivery (all from `app/data.py`)
- FAQ state answers English + Roman-Urdu ("delivery charges kitne hain", "cod hoga")
- stays in FAQ across multiple questions (session memory)
- 2 unrecognised inputs in a row → auto handoff (stuck signal)
- "agent"/"human"/"numainda" → handoff from any state
- per-user isolation (two numbers keep separate state)
- full run through the live HTTP webhook, not just unit calls

## Next
- Swap `app/data.py` for Dev 4's Supabase services once its schema/seed are aligned.
- Optional: render the main menu as an interactive WhatsApp list (senders already
  support `send_list`) instead of a numbered text menu.
- Optional: persist `Context` via Dev 4's `BotSession` so sessions survive restarts.
