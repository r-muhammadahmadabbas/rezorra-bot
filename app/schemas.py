"""The one message shape the rest of the team codes against.

Devs 2-4 should never touch Meta's raw JSON - they only ever see IncomingMessage.
"""
from dataclasses import dataclass, field
from typing import Any, Literal, Optional

MessageType = Literal["text", "button", "list", "unsupported"]


@dataclass
class IncomingMessage:
    """A single inbound WhatsApp message, normalised."""

    user_id: str                      # sender's WhatsApp number, e.g. "923001234567"
    message_id: str                   # Meta's "wamid.xxx" - used for de-duplication
    type: MessageType
    timestamp: int                    # unix seconds
    text: Optional[str] = None        # body for type="text"
    reply_id: Optional[str] = None    # id of the tapped button / list row
    reply_title: Optional[str] = None # visible label of that button / row
    profile_name: Optional[str] = None
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def is_interactive(self) -> bool:
        return self.type in ("button", "list")

    @property
    def value(self) -> str:
        """What the user 'said' - the reply id for taps, the text otherwise.

        Match on this. For taps it is the stable id, never the visible label.
        """
        return self.reply_id if self.is_interactive else (self.text or "")
