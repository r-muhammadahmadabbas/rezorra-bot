"""Loads the merchant catalog from Supabase into app.data.ACTIVE.

Called once at startup and by the /admin/refresh endpoint. On any failure (no
DATABASE_URL, DB unreachable, empty tables) it leaves the offline SEED in place
and logs why - the bot keeps working either way.
"""
import logging

from app import data
from app.db import engine as db_engine

log = logging.getLogger("rezorra.catalog")


async def load_catalog() -> str:
    """Refresh app.data.ACTIVE from the DB. Returns the resulting source name."""
    if not db_engine.is_configured():
        log.info("DATABASE_URL not set - using offline seed catalog")
        data.set_active(data.SEED)
        return "seed"

    try:
        catalog = await _load_from_db()
    except Exception as exc:  # connection, auth, schema - never crash the bot
        log.warning("catalog load from DB failed (%s) - keeping seed", exc)
        data.set_active(data.SEED)
        return "seed (db error)"

    if not catalog.products and not catalog.faqs:
        log.warning("DB returned no products/FAQs - keeping seed")
        data.set_active(data.SEED)
        return "seed (db empty)"

    # Fill any gaps from the seed so the menu/escalation always work.
    if not catalog.menu:
        catalog.menu = data.SEED.menu
    if not catalog.escalation_keywords:
        catalog.escalation_keywords = data.SEED.escalation_keywords

    data.set_active(catalog)
    log.info("catalog loaded from Supabase: %d products, %d FAQs",
             len(catalog.products), len(catalog.faqs))
    return "supabase"


async def _load_from_db() -> data.Catalog:
    from app.db import services

    factory = db_engine.get_session_factory()
    async with factory() as db:
        business_id = await services.get_default_business_id(db)
        if not business_id:
            return data.Catalog()

        db_products = await services.get_products(db, business_id)
        variants = await services.get_variants(db, [str(p.id) for p in db_products])
        db_faqs = await services.get_faqs(db, business_id)
        db_menu = await services.get_menu_options(db, business_id)
        db_rules = await services.get_escalation_rules(db, business_id)

    # Aggregate variants (size/color/stock rows) into the flat Product shape.
    sizes_by_product: dict[str, list[str]] = {}
    stock_by_product: dict[str, int] = {}
    for v in variants:
        pid = str(v.product_id)
        if v.size and v.size not in sizes_by_product.setdefault(pid, []):
            sizes_by_product[pid].append(v.size)
        stock_by_product[pid] = stock_by_product.get(pid, 0) + int(v.stock_quantity or 0)

    products = [
        data.Product(
            name=p.name,
            price=float(p.sale_price or p.base_price or 0),
            sizes=sizes_by_product.get(str(p.id), []),
            stock=stock_by_product.get(str(p.id), 0),
            description=p.description or "",
        )
        for p in db_products
    ]

    faqs = [
        data.Faq(question=f.question or "", answer=f.answer or "",
                 keywords=[k.lower() for k in (f.keywords or [])])
        for f in db_faqs
    ]

    # Prefer target_intent, fall back to option_key; de-dupe + number in build_menu.
    menu_pairs = [
        (m.target_intent or m.option_key or "", m.label or "")
        for m in sorted(db_menu, key=lambda x: (x.sort_order or 0))
    ]
    menu = data.build_menu(menu_pairs)

    escalation_keywords: list[str] = []
    for r in db_rules:
        escalation_keywords += [k.lower() for k in (r.keywords or [])]

    return data.Catalog(
        products=products,
        faqs=faqs,
        menu=menu,
        escalation_keywords=escalation_keywords,
        source="supabase",
    )
