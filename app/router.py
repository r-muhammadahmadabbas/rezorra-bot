"""Where Dev 3 (state machine) and Dev 4 (menu / FAQ / handoff) plug in.

The contract is one function:

    from app.router import on_message_received

    @on_message_received
    async def handle(msg: IncomingMessage, wa: Sender) -> None:
        ...

`msg` is already normalised, `wa` is already wired to mock or Cloud API. Nothing in
here knows about sessions, FAQs or the database - that stays on your side.

If no handler is registered the bot echoes, which is the Day-1 smoke test.
"""
import logging
from typing import Awaitable, Callable

from app.schemas import IncomingMessage
from app.senders.base import Sender

log = logging.getLogger(__name__)

Handler = Callable[[IncomingMessage, Sender], Awaitable[None]]

_handler: Handler | None = None


def on_message_received(fn: Handler) -> Handler:
    """Register the single message handler. Usable as a decorator."""
    global _handler
    if _handler is not None:
        log.warning("replacing existing handler %s with %s", _handler.__name__, fn.__name__)
    _handler = fn
    log.info("handler registered: %s", fn.__name__)
    return fn


async def dispatch(msg: IncomingMessage, wa: Sender) -> None:
    """Hand a message to the registered handler, or echo if there is none."""
    if _handler is None:
        await _echo(msg, wa)
        return

    try:
        await _handler(msg, wa)
    except Exception:
        # One bad message must never kill the webhook loop.
        log.exception("handler failed for message_id=%s", msg.message_id)
        await wa.send_text(
            msg.user_id,
            "Sorry, something went wrong on our side. Please try again.",
        )


async def _echo(msg: IncomingMessage, wa: Sender) -> None:
    if msg.type == "unsupported":
        await wa.send_text(msg.user_id, "Sorry, I can only read text and menu taps for now.")
        return
    await wa.send_text(msg.user_id, f"Echo: {msg.value}")
