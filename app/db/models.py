"""SQLAlchemy models - mirrors Dev 2's Supabase schema (from Rezorra_dev4-week1).

Only the tables the bot reads/writes are declared. Column names and types match
the live tables so queries line up exactly.
"""
from datetime import datetime
import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Business(Base):
    __tablename__ = "businesses"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, index=True)
    whatsapp_number = Column(String)
    currency = Column(String)
    cod_enabled = Column(Boolean)
    created_at = Column(DateTime, default=datetime.utcnow)


class Product(Base):
    __tablename__ = "products"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"))
    category_id = Column(UUID(as_uuid=True), nullable=True)
    name = Column(String, index=True)
    description = Column(String)
    base_price = Column(Float)
    sale_price = Column(Float)
    is_active = Column(Boolean, default=True)
    tags = Column(ARRAY(String))
    best_for = Column(ARRAY(String))
    created_at = Column(DateTime, default=datetime.utcnow)


class ProductVariant(Base):
    __tablename__ = "product_variants"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    sku = Column(String)
    size = Column(String)
    color = Column(String)
    stock_quantity = Column(Integer, default=0)
    is_available = Column(Boolean, default=True)


class FAQEntry(Base):
    __tablename__ = "faq_entries"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"))
    intent = Column(String)
    question = Column(String)
    answer = Column(Text)
    keywords = Column(ARRAY(String))
    is_active = Column(Boolean, default=True)


class DeliveryZone(Base):
    __tablename__ = "delivery_zones"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"))
    city = Column(String)
    delivery_fee = Column(Float)
    estimated_days = Column(String)
    cod_available = Column(Boolean, default=True)


class EscalationRule(Base):
    __tablename__ = "escalation_rules"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"))
    rule_name = Column(String)
    keywords = Column(ARRAY(String))
    reason = Column(String)
    is_active = Column(Boolean, default=True)


class MenuOption(Base):
    __tablename__ = "menu_options"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"))
    option_key = Column(String)
    label = Column(String)
    description = Column(String)
    target_intent = Column(String)
    sort_order = Column(Integer)
    is_active = Column(Boolean, default=True)
