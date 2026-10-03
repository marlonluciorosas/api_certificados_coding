"""Regras de negócio dos eventos (RN03, RN05, RN07, RN09 e RC01)."""
from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Any, Optional

from ..database.converters import ensure_utc, now_utc
from ..database.session import get_connection, transaction
from ..models.entities import Event
from ..repositories import course_repository, event_repository
from .errors import ConflictError, ForbiddenError, NotFoundError, RuleError
from .permissions import get_actor, require_event_manager, require_managers_user

# Campos que não podem mudar depois que o evento termina (RN07).
STRUCTURAL_FIELDS = {
    "start_at",
    "location",
    "capacity",
    "duration_hours",
    "responsible_id",
    "course_id",
}


def get_event(event_id: int) -> Event:
    connection = get_connection()
    try:
        event = event_repository.get_event_by_id(connection, event_id)
        if event is None:
            raise NotFoundError("Evento não encontrado.")
        return event
    finally:
        connection.close()


def list_events(
    *,
    limit: int,
    offset: int = 0,
    course_id: Optional[int] = None,
    search: Optional[str] = None,
    future_only: bool = False,
) -> list[Event]:
    connection = get_connection()
    try:
        return event_repository.list_events(
            connection,
            limit=limit,
            offset=offset,
            course_id=course_id,
            search=search,
            future_only=future_only,
        )
    finally:
        connection.close()


def count_events(*, course_id: Optional[int] = None) -> int:
    connection = get_connection()
    try:
        return event_repository.count_events(connection, course_id=course_id)
    finally:
        connection.close()


def create_event(
    *,
    actor_id: int,
    title: str,
    description: str,
    start_at: datetime,
    location: str,
    capacity: int,
    duration_hours: float,
    responsible_id: int,
    course_id: Optional[int] = None,
) -> Event:
    """Cadastra o evento (RN05: nada de data no passado)."""
    start = ensure_utc(start_at)
    if start < now_utc():
        raise RuleError("Não é permitido cadastrar evento com data/horário passado.")

    try:
        with transaction() as connection:
            actor = get_actor(connection, actor_id)
            if not actor.is_staff:
                # RN03 (mesma ideia): só equipe cadastra eventos.
                raise ForbiddenError(
                    "Somente Administrador ou Professor pode cadastrar eventos."
                )

            require_managers_user(connection, responsible_id)

            if course_id is not None and course_repository.get_course_by_id(
                connection, course_id
            ) is None:
                raise RuleError("O curso informado não existe.")

            event_id = event_repository.insert_event(
                connection,
                title=title,
                description=description,
                start_at=start,
                location=location,
                capacity=capacity,
                duration_hours=duration_hours,
                responsible_id=responsible_id,
                course_id=course_id,
                created_at=now_utc(),
            )
            event = event_repository.get_event_by_id(connection, event_id)
            assert event is not None
            return event
    except sqlite3.IntegrityError as error:
        raise RuleError("Os dados do evento violam uma restrição de integridade.") from error


def update_event(*, actor_id: int, event_id: int, changes: dict[str, Any]) -> Event:
    """Edita o evento respeitando as RN03, RN05 e RN07."""
    if not changes:
        return get_event(event_id)

    with transaction() as connection:
        event = event_repository.get_event_by_id(connection, event_id)
        if event is None:
            raise NotFoundError("Evento não encontrado.")

        require_event_manager(connection, actor_id, event)

        if any(value is None for value in changes.values()):
            raise RuleError("Os campos enviados na edição não podem receber valor nulo.")

        if event.finished and STRUCTURAL_FIELDS.intersection(changes):
            raise ConflictError(
                "Evento finalizado não pode ter data, local, capacidade, carga horária, "
                "responsável ou curso alterados."
            )

        if "start_at" in changes:
            start = ensure_utc(changes["start_at"])
            if start < now_utc():
                raise RuleError("Não é permitido editar evento para data/horário passado.")
            changes["start_at"] = start

        if "responsible_id" in changes:
            require_managers_user(connection, changes["responsible_id"])

        if "course_id" in changes and course_repository.get_course_by_id(
            connection, changes["course_id"]
        ) is None:
            raise RuleError("O curso informado não existe.")

        if "capacity" in changes:
            ativos = event_repository.count_active_registrations(connection, event_id)
            if changes["capacity"] < ativos:
                raise ConflictError(
                    "A nova capacidade não pode ser menor que o total de inscrições ativas."
                )

        event_repository.update_event_fields(connection, event_id, changes)
        updated = event_repository.get_event_by_id(connection, event_id)
        assert updated is not None
        return updated


def delete_event(*, actor_id: int, event_id: int) -> None:
    """Exclui o evento (RN03 e RC01)."""
    with transaction() as connection:
        event = event_repository.get_event_by_id(connection, event_id)
        if event is None:
            raise NotFoundError("Evento não encontrado.")

        require_event_manager(connection, actor_id, event)

        # RC01: evita apagar inscrições "sem querer" junto com o evento
        # (a chave estrangeira tem ON DELETE CASCADE).
        ativos = event_repository.count_active_registrations(connection, event_id)
        if ativos > 0:
            raise ConflictError(
                "Não é possível excluir um evento com inscrições ativas. "
                "Cancele as inscrições ou mude o status do evento antes."
            )

        event_repository.delete_event(connection, event_id)


def count_active_registrations(event_id: int) -> int:
    connection = get_connection()
    try:
        return event_repository.count_active_registrations(connection, event_id)
    finally:
        connection.close()
