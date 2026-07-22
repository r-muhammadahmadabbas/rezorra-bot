"""Real WhatsApp Cloud API sender.

Swapping MockSender for this is the only change needed once Meta credentials land -
set WHATSAPP_MODE=cloud in .env.
"""
import logging

import httpx

from app.config import settings
from app.senders.base import (
    Button,
    Row,
    Sender,
    validate_buttons,
    validate_rows,
    validate_text,
)

log = logging.getLogger(__name__)

TIMEOUT = httpx.Timeout(10.0)


class CloudAPISender(Sender):
    def __init__(self) -> None:
        if not settings.WHATSAPP_TOKEN or not settings.WHATSAPP_PHONE_NUMBER_ID:
            raise RuntimeError(
                "WHATSAPP_MODE=cloud but WHATSAPP_TOKEN / WHATSAPP_PHONE_NUMBER_ID are unset"
            )
        self._headers = {
            "Authorization": f"Bearer {settings.WHATSAPP_TOKEN}",
            "Content-Type": "application/json",
        }

    async def _post(self, payload: dict) -> None:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(settings.graph_url, headers=self._headers, json=payload)

        if resp.status_code >= 400:
            # Meta puts the useful part in the body, not the status line.
            log.error("send failed %s: %s", resp.status_code, resp.text)
            resp.raise_for_status()

        log.info("sent to=%s type=%s", payload.get("to"), payload.get("type"))

    async def send_text(self, user_id: str, text: str) -> None:
        validate_text(text)
        await self._post({
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": user_id,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        })

    async def send_buttons(self, user_id: str, body: str, buttons: list[Button]) -> None:
        validate_text(body)
        validate_buttons(buttons)
        await self._post({
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": user_id,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": body},
                "action": {
                    "buttons": [
                        {"type": "reply", "reply": {"id": b.id, "title": b.title}}
                        for b in buttons
                    ]
                },
            },
        })

    async def send_list(
        self,
        user_id: str,
        body: str,
        rows: list[Row],
        button_label: str = "Choose",
        header: str = "",
    ) -> None:
        validate_text(body)
        validate_rows(rows)

        interactive: dict = {
            "type": "list",
            "body": {"text": body},
            "action": {
                "button": button_label,
                "sections": [{
                    "title": "Options",
                    "rows": [
                        {"id": r.id, "title": r.title, "description": r.description}
                        for r in rows
                    ],
                }],
            },
        }
        if header:
            interactive["header"] = {"type": "text", "text": header}

        await self._post({
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": user_id,
            "type": "interactive",
            "interactive": interactive,
        })
