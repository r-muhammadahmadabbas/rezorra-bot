"""Merchant data - served from an in-memory catalog.

The catalog is loaded from Supabase at startup (app/catalog.py). If the DB is not
configured or unreachable, it falls back to the offline SEED below, so the bot
always runs. The conversation states only ever call the sync functions here -
they never touch the database directly, which is what lets Dev 3's synchronous
state machine stay unchanged.

Swap the DB source freely; nothing in the states changes.
"""
from __future__ import annotations

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
class Catalog:
    """Everything the bot needs about one merchant, held in memory."""
    products: list[Product] = field(default_factory=list)
    faqs: list[Faq] = field(default_factory=list)
    menu_options: list[tuple[str, str]] = field(default_factory=list)  # (key, label)
    escalation_keywords: list[str] = field(default_factory=list)
    source: str = "seed"  # "seed" or "supabase"


# --- Offline seed (from Rezorra_dev4-week1/app/seed.py) - the fallback ---

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
    menu_options=[
        ("1", "Prices"), ("2", "Sizes & fit"), ("3", "Stock availability"),
        ("4", "Delivery & COD"), ("5", "Place an order"),
        ("6", "Ask a question (FAQ)"), ("7", "Talk to a human agent"),
    ],
    escalation_keywords=[
        "agent", "human", "representative", "operator", "complaint",
        "numainda", "banda", "bande", "insaan", "baat karao", "baat karni",
    ],
)

# The catalog the bot is currently serving. Replaced by the DB loader at startup.
ACTIVE: Catalog = SEED


def set_active(catalog: Catalog) -> None:
    global ACTIVE
    ACTIVE = catalog


# --- Query functions the states call (read ACTIVE) ---

def match_faq(message: str) -> Faq | None:
    text = message.lower()
    for faq in ACTIVE.faqs:
        if any(kw and kw in text for kw in faq.keywords):
            return faq
    return None


def is_escalation(message: str) -> bool:
    text = message.lower()
    return any(kw and kw in text for kw in ACTIVE.escalation_keywords)


def delivery_answer() -> str:
    # Pull the delivery-related FAQ answers, whatever their source.
    wanted = ("delivery", "cod", "cash on delivery")
    parts = [f.answer for f in ACTIVE.faqs
             if any(w in (f.question + " " + " ".join(f.keywords)).lower() for w in wanted)]
    return "\n".join(parts) if parts else "Please ask us about delivery and we'll help."


# --- Formatting helpers (content centralised, states stay thin) ---

def format_main_menu(header: str = "") -> str:
    lines = [header] if header else []
    lines.append("How can we help you today? Reply with a number:")
    lines += [f"{key}. {label}" for key, label in ACTIVE.menu_options]
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
