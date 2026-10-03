"""Acesso ao banco na tabela de eventos."""
from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Any, Optional

from ..database.converters import to_iso
from ..models.entities import Event

# A contagem de inscritos ativos já vem na consulta (usada nas RN02 e RN07).
EVENT_SELECT = """
SELECT e.*, u.name AS responsible_name, c.name AS course_name,
       (SELECT COUNT(*) FROM registrations r
        WHERE r.event_id = e.id AND r.status = 'inscrita') AS registrations_count
FROM events e
JOIN users u ON u.id = e.responsible_id
LEFT JOIN courses c ON c.id = e.course_id
"""


def insert_event(
    connection: sqlite3.Connection,
    *,
    title: str,
    description: str,
    start_at: datetime,
    location: str,
    capacity: int,
    duration_hours: float,
    responsible_id: int,
    course_id: Optional[int],
    created_at: datetime,
) -> int:
    cursor = connection.execute(
        """
        INSERT INTO events(
            title, description, start_at, location, capacity,
            duration_hours, responsible_id, course_id, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            title,
            description,
            to_iso(start_at),
            location,
            capacity,
            duration_hours,
            responsible_id,
            course_id,
            to_iso(created_at),
        ),
    )
    return int(cursor.lastrowid)


def get_event_by_id(connection: sqlite3.Connection, event_id: int) -> Optional[Event]:
    row = connection.execute(EVENT_SELECT + " WHERE e.id = ?", (event_id,)).fetchone()
    return Event.from_row(row) if row else None


def list_events(
    connection: sqlite3.Connection,
    *,
    limit: int,
    offset: int,
    course_id: Optional[int] = None,
    search: Optional[str] = None,
    future_only: bool = False,
) -> list[Event]:
    """Lista eventos em ordem de data, com filtros opcionais."""
    conditions: list[str] = []
    values: list[Any] = []
    if course_id is not None:
        conditions.append("e.course_id = ?")
        values.append(course_id)
    if search:
        text = f"%{search.strip()}%"
        conditions.append(
            "(e.title LIKE ? OR e.description LIKE ? OR e.location LIKE ?)"
        )
        values.extend([text, text, text])
    if future_only:
        conditions.append("e.start_at > datetime('now')")
    where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
    values.extend([limit, offset])
    rows = connection.execute(
        EVENT_SELECT + where + " ORDER BY e.start_at, e.id LIMIT ? OFFSET ?", values
    ).fetchall()
    return [Event.from_row(row) for row in rows]


def count_events(
    connection: sqlite3.Connection,
    *,
    course_id: Optional[int] = None,
    search: Optional[str] = None,
    future_only: bool = False,
) -> int:
    conditions: list[str] = []
    values: list[Any] = []
    if course_id is not None:
        conditions.append("course_id = ?")
        values.append(course_id)
    if search:
        text = f"%{search.strip()}%"
        conditions.append("(title LIKE ? OR description LIKE ? OR location LIKE ?)")
        values.extend([text, text, text])
    if future_only:
        conditions.append("start_at > datetime('now')")
    where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = f"SELECT COUNT(*) AS total FROM events{where}"
    return int(connection.execute(sql, values).fetchone()["total"])


def update_event_fields(
    connection: sqlite3.Connection, event_id: int, changes: dict[str, Any]
) -> None:
    """Monta o UPDATE apenas com os campos enviados.

    Os nomes das colunas vêm do schema Pydantic (lista fechada), por isso não há
    risco de injeção de SQL nesta montagem.
    """
    normalized = {
        field: (to_iso(value) if isinstance(value, datetime) else value)
        for field, value in changes.items()
    }
    assignments = ", ".join(f"{field} = ?" for field in normalized)
    connection.execute(
        f"UPDATE events SET {assignments} WHERE id = ?",
        [*normalized.values(), event_id],
    )


def delete_event(connection: sqlite3.Connection, event_id: int) -> None:
    connection.execute("DELETE FROM events WHERE id = ?", (event_id,))


def count_active_registrations(connection: sqlite3.Connection, event_id: int) -> int:
    row = connection.execute(
        """
        SELECT COUNT(*) AS total FROM registrations
        WHERE event_id = ? AND status = 'inscrita'
        """,
        (event_id,),
    ).fetchone()
    return int(row["total"])
