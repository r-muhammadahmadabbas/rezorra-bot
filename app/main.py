"""FastAPI entrypoint - the WhatsApp webhook.

    GET  /webhook  Meta's one-time verification handshake
    POST /webhook  incoming messages
    GET  /health   local sanity check

Run:  uvicorn app.main:app --reload --port 8000
"""
import hashlib
import hmac
import json
import logging
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, FastAPI, Request, Response

from app import data
from app.catalog import load_catalog
from app.config import settings
from app.dedupe import seen_messages
from app.normalizer import parse_webhook
from app.router import dispatch
from app.senders import get_sender

# Importing this registers the integrated handler (Dev 1 connectivity + Dev 3
# state machine + Dev 2/4 data). Note: `from app import ...`, never `import app.x`
# - that would shadow the FastAPI instance named `app` below.
from app import handlers_bot  # noqa: F401

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("rezorra")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the merchant catalog from Supabase (falls back to seed on any failure).
    source = await load_catalog()
    log.info("catalog source: %s", source)
    yield


app = FastAPI(title="Rezorra WhatsApp Bot", lifespan=lifespan)


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "mode": settings.WHATSAPP_MODE,
        "catalog_source": data.ACTIVE.source,
        "products": len(data.ACTIVE.products),
        "faqs": len(data.ACTIVE.faqs),
    }


@app.post("/admin/refresh")
async def refresh_catalog() -> dict:
    """Reload products/FAQs/menu from Supabase without restarting."""
    source = await load_catalog()
    return {"reloaded": True, "source": source,
            "products": len(data.ACTIVE.products), "faqs": len(data.ACTIVE.faqs)}


# Meta requires a reachable Privacy Policy URL before an app can be set to Live.
PRIVACY_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Rezorra - Privacy Policy</title>
<style>body{font-family:system-ui,sans-serif;max-width:44rem;margin:3rem auto;
padding:0 1rem;line-height:1.6;color:#1a1f2b}h1{font-size:1.6rem}h2{font-size:1.1rem;
margin-top:1.8rem}</style></head><body>
<h1>Rezorra - Privacy Policy</h1>
<p><em>Last updated: 21 July 2026</em></p>

<p>Rezorra is a WhatsApp customer-support assistant operated for internal testing by
Blunder Bot Tech. This policy explains what the service does with message data.</p>

<h2>Information we process</h2>
<ul>
  <li>Your WhatsApp phone number and display name.</li>
  <li>The content of messages you send to our WhatsApp business number.</li>
  <li>Timestamps and message identifiers supplied by WhatsApp.</li>
</ul>

<h2>How we use it</h2>
<p>Message data is used only to answer your enquiry, keep track of where you are in a
conversation, and pass you to a human agent when you ask for one. We do not sell it,
and we do not use it for advertising.</p>

<h2>Sharing</h2>
<p>Messages are delivered through the WhatsApp Business Platform and are therefore
processed by Meta under its own privacy policy. We do not share your data with any
other third party.</p>

<h2>Retention</h2>
<p>This is a prototype used for testing. Message data is held only as long as needed
for that testing and is deleted when the test concludes.</p>

<h2>Your choices</h2>
<p>You can stop the service contacting you at any time by replying STOP. To request
deletion of your data, contact us at the address below.</p>

<h2>Contact</h2>
<p>Blunder Bot Tech - privacy enquiries: muhammadahmadabbas1951@gmail.com</p>
</body></html>"""


@app.get("/privacy")
async def privacy() -> Response:
    return Response(PRIVACY_HTML, media_type="text/html")


@app.get("/webhook")
async def verify(request: Request) -> Response:
    """Meta calls this once when you save the webhook URL in the App Dashboard."""
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge", "")

    if mode == "subscribe" and token == settings.WEBHOOK_VERIFY_TOKEN:
        log.info("webhook verified by Meta")
        return Response(challenge, media_type="text/plain")

    log.warning("webhook verification failed (mode=%s)", mode)
    return Response("verification failed", status_code=403)


@app.post("/webhook")
async def receive(request: Request, background: BackgroundTasks) -> Response:
    """Ack Meta immediately, then process. Slow replies here cause retries."""
    raw = await request.body()

    if not _signature_ok(raw, request.headers.get("X-Hub-Signature-256", "")):
        log.warning("rejected webhook: bad signature")
        return Response("invalid signature", status_code=403)

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        log.warning("rejected webhook: body was not JSON")
        return Response("bad json", status_code=400)

    background.add_task(_process, payload)
    return Response(status_code=200)


def _signature_ok(raw: bytes, header: str) -> bool:
    """Verify X-Hub-Signature-256 (HMAC-SHA256 of the raw body, app secret as key).

    Skipped when META_APP_SECRET is empty, so the fake-webhook script works locally.
    """
    if not settings.META_APP_SECRET:
        return True
    if not header.startswith("sha256="):
        return False

    expected = hmac.new(
        settings.META_APP_SECRET.encode(), raw, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, header.removeprefix("sha256="))


async def _process(payload: dict) -> None:
    """Runs after the 200. Normalise, drop duplicates, hand to the flow engine."""
    wa = get_sender()

    for msg in parse_webhook(payload):
        if seen_messages.already_handled(msg.message_id):
            log.info("duplicate ignored message_id=%s", msg.message_id)
            continue

        log.info("IN  <- %s type=%s value=%r", msg.user_id, msg.type, msg.value)
        await dispatch(msg, wa)
