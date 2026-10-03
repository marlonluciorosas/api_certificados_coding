"""Camada de serviços: é aqui que ficam as regras de negócio."""

from . import (
    auth_service,
    course_service,
    dashboard_service,
    event_service,
    registration_service,
    user_service,
)
from .errors import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    RuleError,
    ServiceError,
    UnauthorizedError,
)

__all__ = [
    "ConflictError",
    "ForbiddenError",
    "NotFoundError",
    "RuleError",
    "ServiceError",
    "UnauthorizedError",
    "auth_service",
    "course_service",
    "dashboard_service",
    "event_service",
    "registration_service",
    "user_service",
]
