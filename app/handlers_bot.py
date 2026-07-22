"""The integration bridge: Dev 1 connectivity  <->  Dev 3 engine  <->  Dev 2/4 data.

Flow for one message:
    1. Load this user's Context (Dev 3 session memory).
    2. Global escalation: an agent/human request from ANY state -> handoff.
    3. Run the state machine for one turn (Dev 3 engine + states, using Dev 2/4 data).
    4. Send the reply back through Dev 1's sender (mock console or real Cloud API).

Registering this handler is all it takes to wire the whole bot together.
"""
import logging

from app import data
from app.conversation.engine import StateMachineEngine
from app.conversation import session_store
from app.conversation.states.handoff import HandoffState
from app.router import on_message_received
from app.schemas import IncomingMessage
from app.senders.base import Sender

log = logging.getLogger("rezorra.bot")

HANDOFF_REPLY = "Connecting you to a team member - they will reply here shortly."


@on_message_received
async def handle(msg: IncomingMessage, wa: Sender) -> None:
    # We only drive the flow from text / menu taps. msg.value is the text for
    # plain messages and the tapped id for interactive replies.
    if msg.type == "unsupported":
        await wa.send_text(msg.user_id, "Sorry, I can only read text and menu replies for now.")
        return

    text = msg.value
    ctx = session_store.get_or_create(msg.user_id)
    if msg.profile_name and not ctx.customer_name:
        ctx.customer_name = msg.profile_name

    # Explicit request for a human wins from any state (unless already handed off).
    if data.is_escalation(text) and not isinstance(ctx.current_state, HandoffState):
        ctx.current_state = HandoffState()
        ctx.unrecognized_count = 0
        log.info("HANDOFF (explicit) user=%s", msg.user_id)
        await wa.send_text(msg.user_id, HANDOFF_REPLY)
        return

    before = ctx.current_state.name
    reply = StateMachineEngine(ctx).process_message(text)
    after = ctx.current_state.name
    log.info("user=%s state %s -> %s", msg.user_id, before, after)

    await wa.send_text(msg.user_id, reply)
