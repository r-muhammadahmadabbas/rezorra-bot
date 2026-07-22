"""Turns Meta's webhook payload into IncomingMessage objects.

Meta nests everything under entry[].changes[].value.messages[]. A single POST can
carry several messages, or none at all (status callbacks look the same from outside).
"""
import logging
from typing import Any

from app.schemas import IncomingMessage

log = logging.getLogger(__name__)


def parse_webhook(payload: dict[str, Any]) -> list[IncomingMessage]:
    """Extract every user message in the payload. Status callbacks are ignored."""
    messages: list[IncomingMessage] = []

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})

            # Delivery/read receipts arrive on the same webhook - not user messages.
            if "messages" not in value:
                continue

            names = _contact_names(value)
            for raw in value["messages"]:
                msg = _parse_message(raw, names)
                if msg is not None:
                    messages.append(msg)

    return messages


def _contact_names(value: dict[str, Any]) -> dict[str, str]:
    """wa_id -> profile name, so we can greet people properly."""
    return {
        c.get("wa_id", ""): c.get("profile", {}).get("name", "")
        for c in value.get("contacts", [])
    }


def _parse_message(raw: dict[str, Any], names: dict[str, str]) -> IncomingMessage | None:
    user_id = raw.get("from")
    message_id = raw.get("id")
    if not user_id or not message_id:
        log.warning("skipping message with no from/id: %s", raw)
        return None

    common = {
        "user_id": user_id,
        "message_id": message_id,
        "timestamp": int(raw.get("timestamp", 0)),
        "profile_name": names.get(user_id) or None,
        "raw": raw,
    }

    kind = raw.get("type")

    if kind == "text":
        return IncomingMessage(type="text", text=raw["text"]["body"], **common)

    if kind == "interactive":
        interactive = raw.get("interactive", {})
        itype = interactive.get("type")

        if itype == "button_reply":
            reply = interactive["button_reply"]
            return IncomingMessage(
                type="button", reply_id=reply.get("id"),
                reply_title=reply.get("title"), **common,
            )

        if itype == "list_reply":
            reply = interactive["list_reply"]
            return IncomingMessage(
                type="list", reply_id=reply.get("id"),
                reply_title=reply.get("title"), **common,
            )

    # Images, audio, location, template button taps, etc. The flow engine decides
    # what to do with these - usually "sorry, please use the menu".
    log.info("unsupported message type=%s from=%s", kind, user_id)
    return IncomingMessage(type="unsupported", **common)
