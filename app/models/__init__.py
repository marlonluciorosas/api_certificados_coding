"""Modelos de domínio usados pelas camadas de repositório e serviço."""

from .entities import (
    Course,
    Event,
    Registration,
    RegistrationStatus,
    User,
    UserRole,
)

__all__ = [
    "Course",
    "Event",
    "Registration",
    "RegistrationStatus",
    "User",
    "UserRole",
]