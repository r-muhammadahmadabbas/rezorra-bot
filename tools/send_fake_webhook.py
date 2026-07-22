"""Fake Meta webhooks, so the whole team can test with no Meta account.

Start the server first:
    uvicorn app.main:app --reload --port 8000

Then, in another terminal:
    python tools/send_fake_webhook.py text "hi"
    python tools/send_fake_webhook.py text "I want an agent"
    python tools/send_fake_webhook.py list price
    python tools/send_fake_webhook.py button menu
    python tools/send_fake_webhook.py duplicate      # same id twice - only one reply

Replies print in the server terminal (mock mode).
"""
import hashlib
import hmac
import json
import os
import sys
import time
import uuid

import httpx
from dotenv import load_dotenv

load_dotenv()

URL = os.getenv("WEBHOOK_URL", "http://localhost:8000/webhook")
APP_SECRET = os.getenv("META_APP_SECRET", "")
TEST_USER = os.getenv("TEST_USER_ID", "923001234567")
TEST_NAME = os.getenv("TEST_USER_NAME", "Ahmad")


def _envelope(message: dict) -> dict:
    """Wrap a message in Meta's entry/changes/value structure."""
    return {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "0",
            "changes": [{
                "field": "messages",
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {"display_phone_number": "15550000000",
                                 "phone_number_id": "TEST_PHONE_NUMBER_ID"},
                    "contacts": [{"profile": {"name": TEST_NAME}, "wa_id": TEST_USER}],
                    "messages": [message],
                },
            }],
        }],
    }


def _base(message_id: str | None = None) -> dict:
    return {
        "from": TEST_USER,
        "id": message_id or f"wamid.FAKE{uuid.uuid4().hex[:12]}",
        "timestamp": str(int(time.time())),
    }


def text_message(body: str, message_id: str | None = None) -> dict:
    return _envelope({**_base(message_id), "type": "text", "text": {"body": body}})


def button_message(reply_id: str, title: str = "") -> dict:
    return _envelope({**_base(), "type": "interactive", "interactive": {
        "type": "button_reply",
        "button_reply": {"id": reply_id, "title": title or reply_id.title()},
    }})


def list_message(reply_id: str, title: str = "") -> dict:
    return _envelope({**_base(), "type": "interactive", "interactive": {
        "type": "list_reply",
        "list_reply": {"id": reply_id, "title": title or reply_id.title(),
                       "description": ""},
    }})


def status_callback() -> dict:
    """A delivery receipt - the bot must ignore these, not reply to them."""
    return {
        "object": "whatsapp_business_account",
        "entry": [{"id": "0", "changes": [{"field": "messages", "value": {
            "messaging_product": "whatsapp",
            "metadata": {"display_phone_number": "15550000000",
                         "phone_number_id": "TEST_PHONE_NUMBER_ID"},
            "statuses": [{"id": "wamid.X", "status": "delivered",
                          "timestamp": str(int(time.time())), "recipient_id": TEST_USER}],
        }}]}],
    }


def post(payload: dict) -> None:
    raw = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"}

    # Only sign if a secret is configured - matches the server's behaviour.
    if APP_SECRET:
        digest = hmac.new(APP_SECRET.encode(), raw, hashlib.sha256).hexdigest()
        headers["X-Hub-Signature-256"] = f"sha256={digest}"

    resp = httpx.post(URL, content=raw, headers=headers, timeout=10)
    print(f"-> {URL} returned {resp.status_code}")


def main() -> None:
    args = sys.argv[1:]
    kind = args[0] if args else "text"
    value = args[1] if len(args) > 1 else "hi"

    if kind == "text":
        post(text_message(value))
    elif kind == "button":
        post(button_message(value))
    elif kind == "list":
        post(list_message(value))
    elif kind == "status":
        post(status_callback())
    elif kind == "duplicate":
        fixed = "wamid.FAKEDUPLICATE001"
        print("sending the same message id twice - expect ONE reply")
        post(text_message("hi", fixed))
        post(text_message("hi", fixed))
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
