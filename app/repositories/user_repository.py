"""Acesso ao banco na tabela de usuários.

Os repositórios só sabem SQL: recebem a conexão, executam a consulta e devolvem
objetos do domínio. Nenhuma regra de negócio mora aqui.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Optional

from ..database.converters import to_iso
from ..models.entities import User

# Traz também o nome do curso em uma única consulta (evita N+1).
USER_SELECT = """
SELECT u.*, c.name AS course_name
FROM users u
LEFT JOIN courses c ON c.id = u.course_id
"""


def insert_user(
    connection: sqlite3.Connection,
    *,
    name: str,
    email: str,
    password_hash: str,
    role: str,
    course_id: Optional[int],
    created_at: datetime,
) -> int:
    """Insere o usuário e devolve o id gerado."""
    cursor = connection.execute(
        """
        INSERT INTO users(name, email, password_hash, role, course_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (name, email, password_hash, role, course_id, to_iso(created_at)),
    )
    return int(cursor.lastrowid)


def get_user_by_id(connection: sqlite3.Connection, user_id: int) -> Optional[User]:
    row = connection.execute(USER_SELECT + " WHERE u.id = ?", (user_id,)).fetchone()
    return User.from_row(row) if row else None


def get_user_by_email(connection: sqlite3.Connection, email: str) -> Optional[User]:
    """A coluna email é COLLATE NOCASE, então a comparação ignora maiúsculas."""
    row = connection.execute(USER_SELECT + " WHERE u.email = ?", (email.strip(),)).fetchone()
    return User.from_row(row) if row else None


def list_users(connection: sqlite3.Connection, *, limit: int, offset: int) -> list[User]:
    rows = connection.execute(
        USER_SELECT + " ORDER BY u.name COLLATE NOCASE, u.id LIMIT ? OFFSET ?",
        (limit, offset),
    ).fetchall()
    return [User.from_row(row) for row in rows]


def count_users(connection: sqlite3.Connection) -> int:
    return int(connection.execute("SELECT COUNT(*) AS total FROM users").fetchone()["total"])