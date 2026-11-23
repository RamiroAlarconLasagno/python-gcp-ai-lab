# app/db.py
"""Acceso a PostgreSQL con SQLAlchemy async: tabla quotes, save_quote y get_quote."""

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from functools import lru_cache

from sqlalchemy import DateTime, Integer, Numeric, String
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.config import get_settings
from app.quoting import Quote

QUOTE_VALIDITY = timedelta(hours=48)


class Base(DeclarativeBase):
    """Base de los modelos de SQLAlchemy (la usa Alembic para las migraciones)."""


class QuoteRecord(Base):
    """Cotización guardada: lo pedido, el desglose calculado y su vigencia."""

    __tablename__ = "quotes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    zone: Mapped[str] = mapped_column(String(32))
    mode: Mapped[str] = mapped_column(String(16))
    actual_weight_kg: Mapped[Decimal] = mapped_column(Numeric)
    volumetric_weight_kg: Mapped[Decimal] = mapped_column(Numeric)
    billable_weight_kg: Mapped[Decimal] = mapped_column(Numeric)
    length_cm: Mapped[Decimal] = mapped_column(Numeric)
    width_cm: Mapped[Decimal] = mapped_column(Numeric)
    height_cm: Mapped[Decimal] = mapped_column(Numeric)
    freight: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    urgent_surcharge: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3))
    delivery_days: Mapped[int] = mapped_column(Integer)


@lru_cache
def get_engine() -> AsyncEngine:
    """Crea el engine (pool de conexiones) la primera vez que se usa.

    pool_pre_ping prueba cada conexión antes de usarla: si la base se reinició,
    descarta la conexión muerta y abre otra en vez de responder 500.
    """
    return create_async_engine(get_settings().database_url, pool_pre_ping=True)


def _session() -> AsyncSession:
    """Abre una sesión; expire_on_commit=False deja leer el objeto tras el commit."""
    return async_sessionmaker(get_engine(), expire_on_commit=False)()


async def save_quote(
    *,
    zone: str,
    mode: str,
    length_cm: Decimal,
    width_cm: Decimal,
    height_cm: Decimal,
    quote: Quote,
) -> QuoteRecord:
    """Guarda una cotización calculada; vence 48 horas después de crearse."""
    created_at = datetime.now(UTC)
    record = QuoteRecord(
        id=uuid.uuid4(),
        created_at=created_at,
        expires_at=created_at + QUOTE_VALIDITY,
        zone=zone,
        mode=mode,
        actual_weight_kg=quote.actual_weight_kg,
        volumetric_weight_kg=quote.volumetric_weight_kg,
        billable_weight_kg=quote.billable_weight_kg,
        length_cm=length_cm,
        width_cm=width_cm,
        height_cm=height_cm,
        freight=quote.freight,
        urgent_surcharge=quote.urgent_surcharge,
        total=quote.total,
        currency=quote.currency,
        delivery_days=quote.delivery_days,
    )
    async with _session() as session:
        session.add(record)
        await session.commit()
    return record


async def get_quote(quote_id: uuid.UUID) -> QuoteRecord | None:
    """Devuelve la cotización guardada con ese id, o None si no existe."""
    async with _session() as session:
        return await session.get(QuoteRecord, quote_id)
