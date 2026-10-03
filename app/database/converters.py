"""Conversões de data e hora.

O SQLite guarda texto, então as datas vão para o banco no formato ISO 8601
sempre em UTC. Assim as comparações de data (evento passado, cancelamento com
24h de antecedência) nunca dão erro por causa de fuso horário.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

UTC = timezone.utc


def now_utc() -> datetime:
    """Instante atual em UTC: fonte única de "agora" do sistema."""
    return datetime.now(UTC)


def ensure_utc(value: datetime) -> datetime:
    """Garante que a data tem fuso horário e converte para UTC."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("A data e hora precisam ter fuso horário (ex.: -03:00 ou Z).")
    return value.astimezone(UTC)


def to_iso(value: datetime) -> str:
    """datetime -> texto para gravar no banco."""
    return ensure_utc(value).isoformat()


def from_iso(value: str) -> datetime:
    """Texto do banco -> datetime em UTC."""
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def from_iso_optional(value: Optional[str]) -> Optional[datetime]:
    """Igual ao anterior, mas aceita nulo (usado em cancelled_at)."""
    return from_iso(value) if value else None


def plus_hours(value: datetime, hours: float) -> datetime:
    """Soma horas a uma data (usado para achar o fim do evento)."""
    return value + timedelta(hours=hours)