"""Schemas de inscrição, presença e certificado."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RegistrationCreate(BaseModel):
    """Dados para fazer uma inscrição."""

    user_id: int = Field(gt=0)
    event_id: int = Field(gt=0)


class RegistrationRead(BaseModel):
    """Inscrição devolvida pela API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    user_name: Optional[str] = None
    event_id: int
    event_title: Optional[str] = None
    event_start_at: Optional[datetime] = None
    status: str
    attended: bool
    created_at: datetime
    cancelled_at: Optional[datetime] = None


class AttendanceUpdate(BaseModel):
    """Corpo do PATCH que confirma (ou desfaz) a presença."""

    attended: bool


class CertificateRead(BaseModel):
    """Certificado emitido (RN06)."""

    certificate_id: str
    user_id: int
    participant_name: str
    course_name: Optional[str] = None
    event_id: int
    event_title: str
    workload_hours: float
    issued_at: datetime
    message: str