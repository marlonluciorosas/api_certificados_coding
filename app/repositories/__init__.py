"""Camada de repositórios: somente SQL, sem regra de negócio."""

from . import (
    course_repository,
    event_repository,
    registration_repository,
    user_repository,
)

__all__ = [
    "course_repository",
    "event_repository",
    "registration_repository",
    "user_repository",
]