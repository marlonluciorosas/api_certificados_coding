"""Acesso ao banco na tabela de inscrições."""
from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Any, Optional

from ..database.converters import to_iso
from ..models.entities import Registration

REGISTRATION_SELECT = """
SELECT r.*, u.name AS user_name, e.title AS event_title,
       e.start_at AS event_start_at, e.responsible_id AS event_responsible_id
FROM registrations r
JOIN users u ON u.id = r.user_id
JOIN events e ON e.id = r.event_id
"""


def insert_registration(
    connection: sqlite3.Connection,
    *,
    user_id: int,
    event_id: int,
    created_at: datetime,
) -> int:
    cursor = connection.execute(
        """
        INSERT INTO registrations(user_id, event_id, status, attended, created_at)
        VALUES (?, ?, 'inscrita', 0, ?)
        """,
        (user_id, event_id, to_iso(created_at)),
    )
    return int(cursor.lastrowid)


def get_registration_by_id(
    connection: sqlite3.Connection, registration_id: int
) -> Optional[Registration]:
    row = connection.execute(
        REGISTRATION_SELECT + " WHERE r.id = ?", (registration_id,)
    ).fetchone()
    return Registration.from_row(row) if row else None


def find_by_user_and_event(
    connection: sqlite3.Connection, user_id: int, event_id: int
) -> Optional[Registration]:
    """Usada na RN01: existe inscrição deste usuário neste evento?"""
    row = connection.execute(
        REGISTRATION_SELECT + " WHERE r.user_id = ? AND r.event_id = ?",
        (user_id, event_id),
    ).fetchone()
    return Registration.from_row(row) if row else None


def list_registrations(
    connection: sqlite3.Connection,
    *,
    limit: int,
    offset: int,
    user_id: Optional[int] = None,
    event_id: Optional[int] = None,
    status: Optional[str] = None,
) -> list[Registration]:
    clauses: list[str] = []
    values: list[Any] = []
    if user_id is not None:
        clauses.append("r.user_id = ?")
        values.append(user_id)
    if event_id is not None:
        clauses.append("r.event_id = ?")
        values.append(event_id)
    if status is not None:
        clauses.append("r.status = ?")
        values.append(status)
    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    values.extend([limit, offset])
    rows = connection.execute(
        REGISTRATION_SELECT + where + " ORDER BY r.created_at, r.id LIMIT ? OFFSET ?",
        values,
    ).fetchall()
    return [Registration.from_row(row) for row in rows]


def count_registrations(
    connection: sqlite3.Connection,
    *,
    user_id: Optional[int] = None,
    event_id: Optional[int] = None,
) -> int:
    clauses: list[str] = []
    values: list[Any] = []
    if user_id is not None:
        clauses.append("user_id = ?")
        values.append(user_id)
    if event_id is not None:
        clauses.append("event_id = ?")
        values.append(event_id)
    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    row = connection.execute(
        f"SELECT COUNT(*) AS total FROM registrations{where}", values
    ).fetchone()
    return int(row["total"])


def cancel_registration(
    connection: sqlite3.Connection, registration_id: int, cancelled_at: datetime
) -> None:
    """Só cancela quem ainda está 'inscrita' (proteção contra duplo cancelamento)."""
    connection.execute(
        """
        UPDATE registrations
        SET status = 'cancelada', cancelled_at = ?
        WHERE id = ? AND status = 'inscrita'
        """,
        (to_iso(cancelled_at), registration_id),
    )


def set_attendance(
    connection: sqlite3.Connection, registration_id: int, attended: bool
) -> None:
    connection.execute(
        "UPDATE registrations SET attended = ? WHERE id = ?",
        (1 if attended else 0, registration_id),
    )


def delete_registration(connection: sqlite3.Connection, registration_id: int) -> None:
    connection.execute("DELETE FROM registrations WHERE id = ?", (registration_id,))