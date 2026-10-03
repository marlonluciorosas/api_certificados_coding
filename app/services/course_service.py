"""Regras de negócio dos cursos."""
from __future__ import annotations

import sqlite3
from typing import Optional

from ..database.converters import now_utc
from ..database.session import get_connection, transaction
from ..models.entities import Course
from ..repositories import course_repository
from .errors import ConflictError, NotFoundError
from .permissions import require_managers_user, require_staff


def get_course(course_id: int) -> Course:
    connection = get_connection()
    try:
        course = course_repository.get_course_by_id(connection, course_id)
        if course is None:
            raise NotFoundError("Curso não encontrado.")
        return course
    finally:
        connection.close()


def list_courses(*, limit: int, offset: int = 0) -> list[Course]:
    connection = get_connection()
    try:
        return course_repository.list_courses(connection, limit=limit, offset=offset)
    finally:
        connection.close()


def count_courses() -> int:
    connection = get_connection()
    try:
        return course_repository.count_courses(connection)
    finally:
        connection.close()


def create_course(
    *, actor_id: int, name: str, code: str, coordinator_id: Optional[int] = None
) -> Course:
    """Cadastra o curso; a sigla é única e o coordenador precisa ser da equipe."""
    code = code.strip().upper()

    try:
        with transaction() as connection:
            # Somente Administrador ou Professor cadastra curso.
            require_staff(connection, actor_id)

            if coordinator_id is not None:
                require_managers_user(connection, coordinator_id)

            if course_repository.get_course_by_code(connection, code) is not None:
                raise ConflictError("Já existe um curso cadastrado com esta sigla.")

            course_id = course_repository.insert_course(
                connection,
                name=name,
                code=code,
                coordinator_id=coordinator_id,
                created_at=now_utc(),
            )
            course = course_repository.get_course_by_id(connection, course_id)
            assert course is not None  # acabou de ser inserido
            return course
    except sqlite3.IntegrityError as error:
        raise ConflictError("Já existe um curso cadastrado com esta sigla.") from error