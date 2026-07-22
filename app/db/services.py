"""Async read services (Dev 4's saved SQL queries, as functions).

These run in the async layer only (startup / refresh), never inside a state.
Each takes an AsyncSession. Write services (customer/order/session) are left for
the order flow, which is out of scope this week.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Business,
    DeliveryZone,
    EscalationRule,
    FAQEntry,
    MenuOption,
    Product,
    ProductVariant,
)


async def get_default_business_id(db: AsyncSession) -> str | None:
    row = (await db.execute(select(Business).limit(1))).scalars().first()
    return str(row.id) if row else None


async def get_menu_options(db: AsyncSession, business_id: str) -> list[MenuOption]:
    stmt = (
        select(MenuOption)
        .where(MenuOption.business_id == business_id, MenuOption.is_active.is_(True))
        .order_by(MenuOption.sort_order)
    )
    return list((await db.execute(stmt)).scalars().all())


async def get_products(db: AsyncSession, business_id: str) -> list[Product]:
    stmt = select(Product).where(
        Product.business_id == business_id, Product.is_active.is_(True)
    )
    return list((await db.execute(stmt)).scalars().all())


async def get_variants(db: AsyncSession, product_ids: list[str]) -> list[ProductVariant]:
    if not product_ids:
        return []
    stmt = select(ProductVariant).where(ProductVariant.product_id.in_(product_ids))
    return list((await db.execute(stmt)).scalars().all())


async def get_faqs(db: AsyncSession, business_id: str) -> list[FAQEntry]:
    stmt = select(FAQEntry).where(
        FAQEntry.business_id == business_id, FAQEntry.is_active.is_(True)
    )
    return list((await db.execute(stmt)).scalars().all())


async def get_escalation_rules(db: AsyncSession, business_id: str) -> list[EscalationRule]:
    stmt = select(EscalationRule).where(
        EscalationRule.business_id == business_id, EscalationRule.is_active.is_(True)
    )
    return list((await db.execute(stmt)).scalars().all())


async def get_delivery_zones(db: AsyncSession, business_id: str) -> list[DeliveryZone]:
    stmt = select(DeliveryZone).where(DeliveryZone.business_id == business_id)
    return list((await db.execute(stmt)).scalars().all())
