"""Regras de negócio dos usuários (RN08 e regras de senha)."""
from __future__ import annotations

import sqlite3
from typing import Optional

from ..core.config import settings
from ..core.security import hash_password
from ..database.converters import now_utc
from ..database.session import get_connection, transaction
from ..models.entities import User
from ..repositories import course_repository, user_repository
from .errors import ConflictError, NotFoundError, RuleError


def validate_password(password: str) -> None:
    """Confere o tamanho e a mistura de letras e números da senha (RS03)."""
    if len(password) < settings.password_min_length:
        raise RuleError(
            f"A senha deve ter no mínimo {settings.password_min_length} caracteres."
        )
    if not any(char.isalpha() for char in password):
        raise RuleError("A senha deve conter pelo menos uma letra.")
    if not any(char.isdigit() for char in password):
        raise RuleError("A senha deve conter pelo menos um número.")


def get_user(user_id: int) -> User:
    connection = get_connection()
    try:
        user = user_repository.get_user_by_id(connection, user_id)
        if user is None:
            raise NotFoundError("Usuário não encontrado.")
        return user
    finally:
        connection.close()


def list_users(*, limit: int, offset: int = 0) -> list[User]:
    connection = get_connection()
    try:
        return user_repository.list_users(connection, limit=limit, offset=offset)
    finally:
        connection.close()


def count_users() -> int:
    connection = get_connection()
    try:
        return user_repository.count_users(connection)
    finally:
        connection.close()


def create_user(
    *,
    name: str,
    email: str,
    password: str,
    role: str,
    course_id: Optional[int] = None,
) -> User:
    """Cadastra o usuário guardando apenas o hash da senha."""
    validate_password(password)
    email = email.strip().lower()

    try:
        with transaction() as connection:
            if course_id is not None and course_repository.get_course_by_id(
                connection, course_id
            ) is None:
                raise RuleError("O curso informado não existe.")

            # RN08: e-mail é único. A checagem é antecipada, mas a restrição
            # UNIQUE da tabela continua valendo como garantia final.
            if user_repository.get_user_by_email(connection, email) is not None:
                raise ConflictError("Já existe um usuário cadastrado com este e-mail.")

            user_id = user_repository.insert_user(
                connection,
                name=name,
                email=email,
                password_hash=hash_password(password),
                role=role,
                course_id=course_id,
                created_at=now_utc(),
            )
            return user_repository.get_user_by_id(connection, user_id)  # type: ignore[return-value]
    except sqlite3.IntegrityError as error:
        raise ConflictError("Já existe um usuário cadastrado com este e-mail.") from error