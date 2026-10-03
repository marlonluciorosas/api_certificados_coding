"""Acesso ao banco na tabela de cursos."""
from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Optional

from ..database.converters import to_iso
from ..models.entities import Course

# Uma subconsulta conta quantos eventos cada curso tem.
COURSE_SELECT = """
SELECT c.*, u.name AS coordinator_name,
       (SELECT COUNT(*) FROM events e WHERE e.course_id = c.id) AS events_count
FROM courses c
LEFT JOIN users u ON u.id = c.coordinator_id
"""


def insert_course(
    connection: sqlite3.Connection,
    *,
    name: str,
    code: str,
    coordinator_id: Optional[int],
    created_at: datetime,
) -> int:
    cursor = connection.execute(
        """
        INSERT INTO courses(name, code, coordinator_id, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (name, code.upper(), coordinator_id, to_iso(created_at)),
    )
    return int(cursor.lastrowid)


def get_course_by_id(connection: sqlite3.Connection, course_id: int) -> Optional[Course]:
    row = connection.execute(COURSE_SELECT + " WHERE c.id = ?", (course_id,)).fetchone()
    return Course.from_row(row) if row else None


def get_course_by_code(connection: sqlite3.Connection, code: str) -> Optional[Course]:
    row = connection.execute(COURSE_SELECT + " WHERE c.code = ?", (code.strip(),)).fetchone()
    return Course.from_row(row) if row else None


def list_courses(connection: sqlite3.Connection, *, limit: int, offset: int) -> list[Course]:
    rows = connection.execute(
        COURSE_SELECT + " ORDER BY c.name COLLATE NOCASE, c.id LIMIT ? OFFSET ?",
        (limit, offset),
    ).fetchall()
    return [Course.from_row(row) for row in rows]


def count_courses(connection: sqlite3.Connection) -> int:
    return int(connection.execute("SELECT COUNT(*) AS total FROM courses").fetchone()["total"])