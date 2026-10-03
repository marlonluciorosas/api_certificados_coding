"""Regras de negócio das inscrições, presenças e certificados.

Aqui estão as regras RN01, RN02, RN03, RN04, RN06 e RN10.
"""
from __future__ import annotations

import sqlite3
from datetime import timedelta
from typing import Optional

from ..database.converters import now_utc
from ..database.session import get_connection, transaction
from ..models.entities import Registration
from ..repositories import event_repository, registration_repository, user_repository
from .errors import ConflictError, ForbiddenError, NotFoundError, RuleError
from .permissions import can_act_for_user, get_actor, require_event_manager

# Tempo mínimo de antecedência para cancelar (RN10).
MIN_HOURS_TO_CANCEL = 24


def _get_registration(connection: sqlite3.Connection, registration_id: int) -> Registration:
    registration = registration_repository.get_registration_by_id(connection, registration_id)
    if registration is None:
        raise NotFoundError("Inscrição não encontrada.")
    return registration


def get_registration(registration_id: int) -> Registration:
    connection = get_connection()
    try:
        return _get_registration(connection, registration_id)
    finally:
        connection.close()


def create_registration(*, actor_id: int, user_id: int, event_id: int) -> Registration:
    """Faz a inscrição aplicando RN01 (duplicidade) e RN02 (vagas)."""
    with transaction(immediate=True) as connection:
        actor = get_actor(connection, actor_id)

        # RN04: participante só inscreve a si mesmo.
        if not can_act_for_user(actor, user_id):
            raise ForbiddenError("Participante só pode realizar a própria inscrição.")

        if user_repository.get_user_by_id(connection, user_id) is None:
            raise NotFoundError("Usuário não encontrado.")

        event = event_repository.get_event_by_id(connection, event_id)
        if event is None:
            raise NotFoundError("Evento não encontrado.")

        if event.finished:
            raise RuleError("Não é possível inscrever-se em evento finalizado.")

        # RN01
        if registration_repository.find_by_user_and_event(connection, user_id, event_id):
            raise ConflictError("O usuário já possui uma inscrição neste evento.")

        # RN02: contagem e inserção na mesma transação (BEGIN IMMEDIATE),
        # então dois pedidos simultâneos não passam pela última vaga.
        ativos = event_repository.count_active_registrations(connection, event_id)
        if ativos >= event.capacity:
            raise ConflictError("O evento atingiu a capacidade máxima de vagas.")

        try:
            registration_id = registration_repository.insert_registration(
                connection, user_id=user_id, event_id=event_id, created_at=now_utc()
            )
        except sqlite3.IntegrityError as error:
            raise ConflictError("Não foi possível concluir a inscrição.") from error

        return _get_registration(connection, registration_id)


def list_registrations(
    *,
    actor_id: int,
    user_id: Optional[int] = None,
    event_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int,
    offset: int = 0,
) -> list[Registration]:
    """Consulta inscrições respeitando o perfil (RS04).

    - Administrador e Professor veem tudo;
    - Participante vê apenas as próprias inscrições.
    """
    connection = get_connection()
    try:
        actor = get_actor(connection, actor_id)
        if actor.is_participant:
            if user_id is not None and user_id != actor.id:
                raise ForbiddenError("Participante só pode consultar as próprias inscrições.")
            user_id = actor.id

        return registration_repository.list_registrations(
            connection,
            limit=limit,
            offset=offset,
            user_id=user_id,
            event_id=event_id,
            status=status,
        )
    finally:
        connection.close()


def count_registrations(*, user_id: Optional[int] = None, event_id: Optional[int] = None) -> int:
    connection = get_connection()
    try:
        return registration_repository.count_registrations(
            connection, user_id=user_id, event_id=event_id
        )
    finally:
        connection.close()


def cancel_registration(*, actor_id: int, registration_id: int) -> Registration:
    """Cancela a inscrição (RN04 e RN10)."""
    with transaction(immediate=True) as connection:
        registration = _get_registration(connection, registration_id)
        actor = get_actor(connection, actor_id)

        if not can_act_for_user(actor, registration.user_id):
            raise ForbiddenError("Participante só pode cancelar a própria inscrição.")

        if not registration.is_active:
            raise ConflictError("A inscrição já está cancelada.")

        if registration.event_start_at is None:
            raise NotFoundError("Não encontrei a data do evento desta inscrição.")

        remaining = registration.event_start_at - now_utc()
        if remaining < timedelta(hours=MIN_HOURS_TO_CANCEL):
            raise RuleError(
                "O cancelamento só é permitido com no mínimo 24 horas de antecedência."
            )

        registration_repository.cancel_registration(connection, registration_id, now_utc())
        return _get_registration(connection, registration_id)


def delete_registration(*, actor_id: int, registration_id: int) -> None:
    """Exclusão definitiva: operação da equipe, diferente do cancelamento (RN03)."""
    with transaction(immediate=True) as connection:
        registration = _get_registration(connection, registration_id)
        event = event_repository.get_event_by_id(connection, registration.event_id)
        if event is None:
            raise NotFoundError("Evento não encontrado.")

        require_event_manager(connection, actor_id, event)
        registration_repository.delete_registration(connection, registration_id)


def update_attendance(
    *, actor_id: int, registration_id: int, attended: bool
) -> Registration:
    """Marca ou desmarca a presença (precisa ser da equipe do evento)."""
    with transaction(immediate=True) as connection:
        registration = _get_registration(connection, registration_id)
        event = event_repository.get_event_by_id(connection, registration.event_id)
        if event is None:
            raise NotFoundError("Evento não encontrado.")

        require_event_manager(connection, actor_id, event)

        if not registration.is_active:
            raise RuleError("Não é possível confirmar presença de inscrição cancelada.")

        registration_repository.set_attendance(connection, registration_id, attended)
        return _get_registration(connection, registration_id)


def issue_certificate(*, actor_id: int, registration_id: int) -> dict:
    """Emite o certificado (RN06: inscrição ativa + presença confirmada)."""
    connection = get_connection()
    try:
        registration = _get_registration(connection, registration_id)
        actor = get_actor(connection, actor_id)
        event = event_repository.get_event_by_id(connection, registration.event_id)
        if event is None:
            raise NotFoundError("Evento não encontrado.")

        can_issue = (
            actor.id == registration.user_id
            or actor.is_admin
            or (actor.is_teacher and actor.id == event.responsible_id)
        )
        if not can_issue:
            raise ForbiddenError(
                "Somente o participante, o responsável pelo evento ou um "
                "Administrador pode emitir o certificado."
            )

        if not registration.is_active or not registration.attended:
            raise RuleError("Certificado condicionado a inscrição ativa e presença confirmada.")

        issued_at = now_utc()
        return {
            "certificate_id": (
                f"CERT-{registration.event_id:04d}-{registration.user_id:04d}"
                f"-{registration.id:06d}"
            ),
            "user_id": registration.user_id,
            "participant_name": registration.user_name,
            "course_name": event.course_name,
            "event_id": registration.event_id,
            "event_title": registration.event_title,
            "workload_hours": event.duration_hours,
            "issued_at": issued_at,
            "message": "Certificado emitido após inscrição ativa e presença confirmada.",
        }
    finally:
        connection.close()