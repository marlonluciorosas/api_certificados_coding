"""Modelos de domínio (as "coisas" do sistema).

Cada classe aqui representa uma linha do banco como um objeto Python:
User, Course, Event e Registration.

Por que não usar o dicionário cru que vem do SQLite? Porque assim:
- o tipo fica claro (start_at é datetime, attended é bool, etc.);
- as contas que dependem do dado (vagas disponíveis, evento finalizado)
  viram propriedades da própria classe, no lugar de ficarem espalhadas.

Os schemas Pydantic que entram e saem na API ficam em `app/schemas`.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from ..database.converters import from_iso, from_iso_optional, now_utc, plus_hours


class UserRole(str, Enum):
    """Perfis de usuário do sistema."""

    PARTICIPANTE = "participante"
    PROFESSOR = "professor"
    ADMIN = "admin"


class RegistrationStatus(str, Enum):
    """Situação de uma inscrição."""

    INSCRITA = "inscrita"
    CANCELADA = "cancelada"


@dataclass(frozen=True)
class User:
    """Usuário do sistema (aluno, professor ou administrador)."""

    id: int
    name: str
    email: str
    password_hash: str
    role: str
    created_at: datetime
    course_id: Optional[int] = None
    course_name: Optional[str] = None

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN.value

    @property
    def is_teacher(self) -> bool:
        return self.role == UserRole.PROFESSOR.value

    @property
    def is_participant(self) -> bool:
        return self.role == UserRole.PARTICIPANTE.value

    @property
    def is_staff(self) -> bool:
        """Administrador e professor são considerados equipe do evento (RN03)."""
        return self.role in (UserRole.ADMIN.value, UserRole.PROFESSOR.value)

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "User":
        keys = row.keys()
        return cls(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            password_hash=row["password_hash"],
            role=row["role"],
            created_at=from_iso(row["created_at"]),
            course_id=row["course_id"] if "course_id" in keys else None,
            course_name=row["course_name"] if "course_name" in keys else None,
        )


@dataclass(frozen=True)
class Course:
    """Curso da faculdade. Todo evento pertence a um curso."""

    id: int
    name: str
    code: str
    coordinator_id: Optional[int]
    created_at: datetime
    coordinator_name: Optional[str] = None
    events_count: int = 0

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Course":
        keys = row.keys()
        return cls(
            id=row["id"],
            name=row["name"],
            code=row["code"],
            coordinator_id=row["coordinator_id"],
            created_at=from_iso(row["created_at"]),
            coordinator_name=row["coordinator_name"] if "coordinator_name" in keys else None,
            events_count=int(row["events_count"]) if "events_count" in keys else 0,
        )


@dataclass(frozen=True)
class Event:
    """Evento cadastrado (workshop, palestra, minicurso...)."""

    id: int
    title: str
    description: str
    start_at: datetime
    location: str
    capacity: int
    duration_hours: float
    responsible_id: int
    created_at: datetime
    course_id: Optional[int] = None
    responsible_name: Optional[str] = None
    course_name: Optional[str] = None
    registrations_count: int = 0

    @property
    def end_at(self) -> datetime:
        """Momento em que o evento termina (início + carga horária)."""
        return plus_hours(self.start_at, self.duration_hours)

    def is_finished_at(self, reference: Optional[datetime] = None) -> bool:
        """Diz se o evento já terminou no momento informado."""
        return self.end_at <= (reference or now_utc())

    @property
    def finished(self) -> bool:
        """Campo usado na resposta da API (RN07)."""
        return self.is_finished_at()

    @property
    def available_spots(self) -> int:
        """Vagas que ainda restam (RN02)."""
        return max(self.capacity - self.registrations_count, 0)

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Event":
        keys = row.keys()
        return cls(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            start_at=from_iso(row["start_at"]),
            location=row["location"],
            capacity=int(row["capacity"]),
            duration_hours=float(row["duration_hours"]),
            responsible_id=row["responsible_id"],
            created_at=from_iso(row["created_at"]),
            course_id=row["course_id"] if "course_id" in keys else None,
            responsible_name=row["responsible_name"] if "responsible_name" in keys else None,
            course_name=row["course_name"] if "course_name" in keys else None,
            registrations_count=(
                int(row["registrations_count"]) if "registrations_count" in keys else 0
            ),
        )


@dataclass(frozen=True)
class Registration:
    """Inscrição de um usuário em um evento."""

    id: int
    user_id: int
    event_id: int
    status: str
    attended: bool
    created_at: datetime
    cancelled_at: Optional[datetime] = None
    user_name: Optional[str] = None
    event_title: Optional[str] = None
    event_start_at: Optional[datetime] = None
    event_responsible_id: Optional[int] = None

    @property
    def is_active(self) -> bool:
        return self.status == RegistrationStatus.INSCRITA.value

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Registration":
        keys = row.keys()
        return cls(
            id=row["id"],
            user_id=row["user_id"],
            event_id=row["event_id"],
            status=row["status"],
            attended=bool(row["attended"]),
            created_at=from_iso(row["created_at"]),
            cancelled_at=from_iso_optional(row["cancelled_at"]),
            user_name=row["user_name"] if "user_name" in keys else None,
            event_title=row["event_title"] if "event_title" in keys else None,
            event_start_at=(
                from_iso(row["event_start_at"]) if "event_start_at" in keys else None
            ),
            event_responsible_id=(
                row["event_responsible_id"] if "event_responsible_id" in keys else None
            ),
        )
