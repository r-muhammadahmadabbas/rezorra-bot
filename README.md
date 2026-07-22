# Rezorra WhatsApp Bot

Dev 1's connectivity layer: the WhatsApp webhook, the normalised message shape, and
the outbound send interface.

**It runs with no Meta account.** In `mock` mode replies print to the console, so
Devs 2-4 can build and test their parts today.

---

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env          # defaults are fine for mock mode
```

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

Then in a second terminal, send fake WhatsApp messages:

```bash
python tools/send_fake_webhook.py text "hi"
python tools/send_fake_webhook.py list price
python tools/send_fake_webhook.py button menu
python tools/send_fake_webhook.py text "I want an agent"
python tools/send_fake_webhook.py duplicate     # sends same id twice -> one reply
python tools/send_fake_webhook.py status        # delivery receipt -> ignored
```

Replies appear in the server terminal.

---

## The contract (Devs 2-4 read this)

Register **one** handler. You get a normalised message and a sender. That's it.

```python
from app.router import on_message_received
from app.schemas import IncomingMessage
from app.senders.base import Sender, Button, Row

@on_message_received
async def handle(msg: IncomingMessage, wa: Sender) -> None:
    if msg.value == "price":
        await wa.send_text(msg.user_id, "Prices start from PKR 2,500")
```

### What you receive - `IncomingMessage`

| Field | Meaning |
|---|---|
| `user_id` | sender's number, e.g. `"923001234567"` - use as the session key |
| `message_id` | Meta's `wamid.xxx` (already de-duplicated for you) |
| `type` | `"text"` \| `"button"` \| `"list"` \| `"unsupported"` |
| `text` | body, for `type="text"` |
| `reply_id` | id of the tapped button/row |
| `reply_title` | visible label of that button/row |
| `profile_name` | WhatsApp display name, may be `None` |
| `timestamp` | unix seconds |
| `raw` | original Meta JSON, if you ever need it |

**`msg.value`** is the shortcut: the `reply_id` for taps, the text otherwise.
**Always match on ids, never on visible labels** - labels change, ids don't.

### What you send - `Sender`

```python
await wa.send_text(user_id, "text")

await wa.send_buttons(user_id, "body", [           # max 3
    Button("menu", "Main menu"),
    Button("agent", "Talk to a person"),
])

await wa.send_list(user_id, "body", [              # max 10
    Row("price", "Price", "Check the price"),
    Row("sizes", "Sizes", "Available sizes"),
], button_label="View options", header="Rezorra")
```

WhatsApp's limits are enforced locally and raise `ValueError`, so you find out on
your machine instead of getting a 400 from Meta:

- 3 buttons max, title <= 20 chars
- 10 rows max, title <= 24 chars, description <= 72 chars
- body <= 1024 chars
- ids must be unique within a message

### Rules

- Handlers must be `async`.
- Exceptions are caught and logged - one bad message won't kill the webhook.
- Don't import `app.main` from your module (circular import).
- Replace `app/handlers_demo.py` with the real handler, and update the import in
  `app/main.py`.

---

## Switching to the real WhatsApp (Dev 1, once Meta clears)

1. Fill in `.env`:
   ```
   WHATSAPP_MODE=cloud
   WHATSAPP_PHONE_NUMBER_ID=...
   WHATSAPP_TOKEN=...            # permanent token, via System User
   META_APP_SECRET=...
   ```
2. Expose the local server: `ngrok http 8000`
3. Meta App Dashboard -> WhatsApp -> Configuration -> Webhook:
   - Callback URL: `https://<ngrok-id>.ngrok-free.app/webhook`
   - Verify token: same value as `WEBHOOK_VERIFY_TOKEN` in `.env`
   - Subscribe to the **messages** field
4. Add the team's numbers as test recipients (max 5, each verified by OTP).

No other code changes. `get_sender()` picks `CloudAPISender` from `WHATSAPP_MODE`.

> ngrok's free URL changes on every restart - re-paste it in the dashboard each time.

---

## Layout

```
app/
  main.py           FastAPI app: GET/POST /webhook, signature check, fast 200
  normalizer.py     Meta JSON -> IncomingMessage
  schemas.py        IncomingMessage
  router.py         on_message_received / dispatch  <- the plug-in seam
  dedupe.py         drops Meta's retries
  handlers_bot.py   the bridge: connectivity <-> state machine <-> data
  data.py           product / FAQ / menu content (Dev 2/4)
  conversation/     state machine (Dev 3): engine, context, session_store, states/
  senders/
    base.py         Sender interface + limits
    mock.py         prints to console
    cloud_api.py    real Graph API
tools/
  send_fake_webhook.py
```

See **INTEGRATION.md** for how the three teammates' codebases were merged.

## Verified working

- `GET /webhook` returns the challenge on a correct verify token, 403 otherwise
- `POST /webhook` rejects a forged `X-Hub-Signature-256` with 403
- Text, button-reply and list-reply messages all normalise and route
- Duplicate `message_id` is processed once
- Delivery/read status callbacks are ignored, not replied to
