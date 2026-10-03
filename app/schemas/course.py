"""Schemas de curso."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CourseCreate(BaseModel):
    """Dados para cadastrar um curso."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=3, max_length=120)
    code: str = Field(min_length=2, max_length=12)
    coordinator_id: Optional[int] = Field(default=None, gt=0)

    @field_validator("code")
    @classmethod
    def upper_code(cls, value: str) -> str:
        """Sigla sempre em maiúsculas para não criar curso repetido (ads x ADS)."""
        return value.upper()


class CourseRead(BaseModel):
    """Curso devolvido pela API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    coordinator_id: Optional[int] = None
    coordinator_name: Optional[str] = None
    events_count: int = 0
    created_at: datetime