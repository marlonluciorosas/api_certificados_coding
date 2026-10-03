"""Schemas de evento."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _check_timezone(value: Optional[datetime]) -> Optional[datetime]:
    """A data precisa ter fuso para as regras de prazo funcionarem (RN05/RN10)."""
    if value is not None and (value.tzinfo is None or value.utcoffset() is None):
        raise ValueError("start_at deve conter fuso horário, por exemplo -03:00 ou Z.")
    return value


class EventCreate(BaseModel):
    """Dados para cadastrar um evento (RN05 e RN09)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=3, max_length=160)
    description: str = Field(default="", max_length=2000)
    start_at: datetime
    location: str = Field(min_length=2, max_length=200)
    capacity: int = Field(gt=0, le=1_000_000)
    duration_hours: float = Field(gt=0, le=720)
    responsible_id: int = Field(gt=0)
    course_id: Optional[int] = Field(default=None, gt=0)

    @field_validator("start_at")
    @classmethod
    def start_must_have_timezone(cls, value: datetime) -> datetime:
        return _check_timezone(value)  # type: ignore[return-value]


class EventUpdate(BaseModel):
    """Campos que podem ser alterados em um PATCH (todos opcionais)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: Optional[str] = Field(default=None, min_length=3, max_length=160)
    description: Optional[str] = Field(default=None, max_length=2000)
    start_at: Optional[datetime] = None
    location: Optional[str] = Field(default=None, min_length=2, max_length=200)
    capacity: Optional[int] = Field(default=None, gt=0, le=1_000_000)
    duration_hours: Optional[float] = Field(default=None, gt=0, le=720)
    responsible_id: Optional[int] = Field(default=None, gt=0)
    course_id: Optional[int] = Field(default=None, gt=0)

    @field_validator("start_at")
    @classmethod
    def start_must_have_timezone(cls, value: Optional[datetime]) -> Optional[datetime]:
        return _check_timezone(value)


class EventRead(BaseModel):
    """Evento devolvido pela API, já com os campos calculados."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    start_at: datetime
    end_at: datetime
    location: str
    capacity: int
    duration_hours: float
    responsible_id: int
    responsible_name: Optional[str] = None
    course_id: Optional[int] = None
    course_name: Optional[str] = None
    registrations_count: int
    available_spots: int
    finished: bool
    created_at: datetime