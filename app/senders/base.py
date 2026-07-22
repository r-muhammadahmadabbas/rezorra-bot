"""The outbound interface Devs 2-4 build against.

Three ways to talk to a user:
    send_text    - plain message
    send_buttons - up to 3 tappable reply buttons
    send_list    - a menu of up to 10 rows (this is the welcome menu)

WhatsApp's limits are enforced here, not at the API, so a mistake fails loudly on
a local machine instead of silently at Meta.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass

# Meta's caps - exceeding any of these is a 400 from the Graph API.
MAX_BUTTONS = 3
MAX_ROWS = 10
MAX_BUTTON_TITLE = 20
MAX_ROW_TITLE = 24
MAX_ROW_DESCRIPTION = 72
MAX_BODY = 1024


@dataclass
class Button:
    """A tappable reply button. `id` is what comes back - keep it stable."""

    id: str
    title: str


@dataclass
class Row:
    """One selectable row inside a list menu."""

    id: str
    title: str
    description: str = ""


class Sender(ABC):
    @abstractmethod
    async def send_text(self, user_id: str, text: str) -> None:
        """Send a plain text message."""

    @abstractmethod
    async def send_buttons(self, user_id: str, body: str, buttons: list[Button]) -> None:
        """Send up to 3 reply buttons."""

    @abstractmethod
    async def send_list(
        self,
        user_id: str,
        body: str,
        rows: list[Row],
        button_label: str = "Choose",
        header: str = "",
    ) -> None:
        """Send a list menu of up to 10 rows."""


def validate_text(body: str) -> None:
    if not body or not body.strip():
        raise ValueError("message body cannot be empty")
    if len(body) > MAX_BODY:
        raise ValueError(f"body is {len(body)} chars, max is {MAX_BODY}")


def validate_buttons(buttons: list[Button]) -> None:
    if not buttons:
        raise ValueError("need at least 1 button")
    if len(buttons) > MAX_BUTTONS:
        raise ValueError(f"{len(buttons)} buttons, WhatsApp allows max {MAX_BUTTONS}")
    ids = [b.id for b in buttons]
    if len(set(ids)) != len(ids):
        raise ValueError(f"button ids must be unique, got {ids}")
    for b in buttons:
        if len(b.title) > MAX_BUTTON_TITLE:
            raise ValueError(f"button title {b.title!r} is over {MAX_BUTTON_TITLE} chars")


def validate_rows(rows: list[Row]) -> None:
    if not rows:
        raise ValueError("need at least 1 row")
    if len(rows) > MAX_ROWS:
        raise ValueError(f"{len(rows)} rows, WhatsApp allows max {MAX_ROWS}")
    ids = [r.id for r in rows]
    if len(set(ids)) != len(ids):
        raise ValueError(f"row ids must be unique, got {ids}")
    for r in rows:
        if len(r.title) > MAX_ROW_TITLE:
            raise ValueError(f"row title {r.title!r} is over {MAX_ROW_TITLE} chars")
        if len(r.description) > MAX_ROW_DESCRIPTION:
            raise ValueError(f"row description for {r.id!r} is over {MAX_ROW_DESCRIPTION} chars")
