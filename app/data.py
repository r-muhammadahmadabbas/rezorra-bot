"""Merchant data - served from an in-memory catalog.

Loaded from Supabase at startup (app/catalog.py); falls back to the offline SEED
if the DB is unreachable/empty. Conversation states only call the sync functions
here, which is what lets Dev 3's synchronous state machine stay unchanged.

The menu is normalised to numbered options routed by *intent*, so it works
whether the DB uses numeric keys or semantic keys ("price", "sizes", ...).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class Product:
    name: str
    price: float
    sizes: list[str]
    stock: int
    description: str = ""


@dataclass
class Faq:
    question: str
    answer: str
    keywords: list[str] = field(default_factory=list)


@dataclass
class MenuItem:
    number: str      # display number the user types, e.g. "1"
    label: str       # what the user sees, e.g. "Prices"
    intent: str      # canonical action: price/sizes/stock/delivery/order/recommendation/faq/agent


# Canonical intents the state machine knows how to handle.
INTENTS = {"price", "sizes", "stock", "delivery", "order", "recommendation", "faq", "agent"}


def canonical_intent(raw: str) -> str | None:
    """Map any DB option_key / target_intent to one canonical intent."""
    t = (raw or "").lower()
    if "recommend" in t:
        return "recommendation"
    if "price" in t:
        return "price"
    if "size" in t:
        return "sizes"
    if "stock" in t:
        return "stock"
    if "deliver" in t:
        return "delivery"
    if "order" in t or "buy" in t or "purchase" in t:
        return "order"
    if "faq" in t or "question" in t:
        return "faq"
    if "agent" in t or "human" in t or "support" in t:
        return "agent"
    return None


@dataclass
class Catalog:
    products: list[Product] = field(default_factory=list)
    faqs: list[Faq] = field(default_factory=list)
    menu: list[MenuItem] = field(default_factory=list)
    escalation_keywords: list[str] = field(default_factory=list)
    source: str = "seed"


# --- Offline seed (fallback) ---

SEED = Catalog(
    products=[
        Product("Floral Lawn Suit", 3850, ["S", "M", "L", "XL"], 45,
                "Premium 3-piece printed lawn suit with chiffon dupatta."),
        Product("Embroidered Kurti", 2490, ["S", "M", "L"], 20,
                "Elegant 1-piece cotton kurti with delicate embroidery."),
        Product("Classic Cotton Trouser", 1450, ["S", "M", "L", "XL"], 60,
                "Slim-fit comfortable cotton trouser."),
        Product("Silk Party Shirt", 4800, ["M", "L"], 5,
                "Luxurious pure silk printed shirt with hand-crafted embellishments."),
    ],
    faqs=[
        Faq("What are your delivery charges?",
            "Delivery is Rs. 200 all across Pakistan. If your order value is above Rs. 3000, delivery is FREE!",
            ["delivery charge", "delivery fee", "shipping", "delivery cost", "free delivery", "delivery kitne"]),
        Faq("Do you support Cash on Delivery (COD)?",
            "Yes! We offer Cash on Delivery (COD) across Pakistan. You pay the rider in cash when your parcel arrives.",
            ["cod", "cash on delivery", "payment", "pay on delivery", "cod hoga", "cod available"]),
        Faq("How long does delivery take?",
            "We process orders within 24 hours. Delivery takes 2-4 working days for major cities and 3-5 days elsewhere.",
            ["delivery time", "how long", "delivery days", "delivery kab", "kitne din"]),
        Faq("What is your return and exchange policy?",
            "We have a 7-day return and exchange policy. Wrong size or a damaged item? Message us and we exchange it free. Tags must stay attached.",
            ["return", "exchange", "replace", "return policy", "size change", "wapis", "replacement"]),
        Faq("Where are you located? Do you have an outlet?",
            "We are an online-only brand based in Karachi and ship from our warehouse. No physical outlet.",
            ["location", "shop", "store", "outlet", "office", "address", "shop kahan"]),
    ],
    menu=[
        MenuItem("1", "Prices", "price"),
        MenuItem("2", "Sizes & fit", "sizes"),
        MenuItem("3", "Stock availability", "stock"),
        MenuItem("4", "Delivery & COD", "delivery"),
        MenuItem("5", "Place an order", "order"),
        MenuItem("6", "Ask a question (FAQ)", "faq"),
        MenuItem("7", "Talk to a human agent", "agent"),
    ],
    escalation_keywords=[
        "agent", "human", "representative", "operator",
        "numainda", "banda", "bande", "insaan", "baat karao", "baat karni",
    ],
)

ACTIVE: Catalog = SEED


def set_active(catalog: Catalog) -> None:
    global ACTIVE
    ACTIVE = catalog


# Preferred display order; anything unknown is appended after these.
MENU_ORDER = ["price", "sizes", "stock", "delivery", "recommendation", "order", "faq", "agent"]

# Default labels used when the DB doesn't supply one (e.g. the injected FAQ option).
DEFAULT_LABELS = {
    "price": "Prices", "sizes": "Sizes & fit", "stock": "Stock availability",
    "delivery": "Delivery & COD", "recommendation": "Product recommendation",
    "order": "Place an order", "faq": "Ask a question (FAQ)", "agent": "Talk to a human agent",
}


def build_menu(pairs: list[tuple[str, str]]) -> list[MenuItem]:
    """Turn (raw_key_or_intent, label) pairs into a clean, de-duplicated, ordered
    and numbered menu keyed by intent. Always includes an FAQ option."""
    label_by_intent: dict[str, str] = {}
    for raw, label in pairs:
        intent = canonical_intent(raw) or canonical_intent(label)
        if intent and intent not in label_by_intent:
            label_by_intent[intent] = label.strip() or DEFAULT_LABELS.get(intent, intent.title())

    # Guarantee an FAQ entry even if the DB has none.
    label_by_intent.setdefault("faq", DEFAULT_LABELS["faq"])

    ordered = sorted(label_by_intent, key=lambda i: MENU_ORDER.index(i) if i in MENU_ORDER else len(MENU_ORDER))
    return [MenuItem(str(n), label_by_intent[intent], intent) for n, intent in enumerate(ordered, 1)]


# --- Query functions the states call ---

def match_faq(message: str) -> Faq | None:
    text = message.lower()
    for faq in ACTIVE.faqs:
        if any(kw and kw in text for kw in faq.keywords):
            return faq
    return None


def is_escalation(message: str) -> bool:
    text = message.lower()
    return any(kw and kw in text for kw in ACTIVE.escalation_keywords)


def menu_item_for(number: str) -> MenuItem | None:
    # Accept "1", " 1 ", "1.", "1)", "(1)" - i.e. a bare number with surrounding
    # punctuation - but NOT "option 1" or "I want 1 shirt".
    m = re.fullmatch(r"\W*(\d{1,3})\W*", number.strip())
    key = m.group(1) if m else number.strip()
    for item in ACTIVE.menu:
        if item.number == key:
            return item
    return None


def delivery_answer() -> str:
    wanted = ("delivery", "cod", "cash on delivery")
    parts = [f.answer for f in ACTIVE.faqs
             if any(w in (f.question + " " + " ".join(f.keywords)).lower() for w in wanted)]
    return "\n".join(parts) if parts else "Please ask us about delivery and we'll help."


# --- Formatting helpers ---

def format_main_menu(header: str = "") -> str:
    lines = [header] if header else []
    lines.append("How can we help you today? Reply with a number:")
    lines += [f"{m.number}. {m.label}" for m in ACTIVE.menu]
    return "\n".join(lines)


def format_prices() -> str:
    lines = ["*Our prices:*"]
    lines += [f"- {p.name}: Rs. {int(p.price)}" for p in ACTIVE.products]
    lines.append("\nType a number for something else, or MENU for the options.")
    return "\n".join(lines)


def format_sizes() -> str:
    lines = ["*Available sizes:*"]
    lines += [f"- {p.name}: {', '.join(p.sizes) if p.sizes else 'N/A'}" for p in ACTIVE.products]
    lines.append("\nType MENU for the options.")
    return "\n".join(lines)


def format_stock() -> str:
    lines = ["*In stock right now:*"]
    for p in ACTIVE.products:
        tag = "Low stock!" if p.stock <= 10 else "In stock"
        lines.append(f"- {p.name}: {p.stock} units ({tag})")
    lines.append("\nType MENU for the options.")
    return "\n".join(lines)


def format_recommendation() -> str:
    lines = ["*Popular picks:*"]
    for p in sorted(ACTIVE.products, key=lambda x: x.stock, reverse=True)[:3]:
        lines.append(f"- {p.name}: Rs. {int(p.price)} ({', '.join(p.sizes) if p.sizes else 'N/A'})")
    lines.append("\nType MENU for the options.")
    return "\n".join(lines)
