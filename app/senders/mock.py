"""Console sender - lets the whole team build and test with no Meta account.

Same validation as the real sender, so anything that works here works on Cloud API.
"""
import logging

from app.senders.base import (
    Button,
    Row,
    Sender,
    validate_buttons,
    validate_rows,
    validate_text,
)

log = logging.getLogger(__name__)


class MockSender(Sender):
    def __init__(self) -> None:
        # Every outbound message, in order. Handy for assertions in tests.
        self.sent: list[dict] = []

    async def send_text(self, user_id: str, text: str) -> None:
        validate_text(text)
        self.sent.append({"to": user_id, "kind": "text", "text": text})
        print(f"\n[OUT -> {user_id}] {text}\n")

    async def send_buttons(self, user_id: str, body: str, buttons: list[Button]) -> None:
        validate_text(body)
        validate_buttons(buttons)
        self.sent.append({"to": user_id, "kind": "buttons", "body": body, "buttons": buttons})
        rendered = "\n".join(f"   [{b.id}] {b.title}" for b in buttons)
        print(f"\n[OUT -> {user_id}] {body}\n{rendered}\n")

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
        self.sent.append(
            {"to": user_id, "kind": "list", "body": body, "rows": rows,
             "button_label": button_label, "header": header}
        )
        rendered = "\n".join(
            f"   [{r.id}] {r.title}" + (f" - {r.description}" if r.description else "")
            for r in rows
        )
        head = f"{header}\n" if header else ""
        print(f"\n[OUT -> {user_id}] {head}{body}\n   ({button_label})\n{rendered}\n")
