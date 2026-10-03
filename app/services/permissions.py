"""Funções de permissão usadas por mais de um serviço.

Ficam separadas para não repetir a mesma verificação em vários arquivos e para
deixar claro em um lugar só "quem pode o quê" (RN03 e RN04).
"""
from __future__ import annotations

import sqlite3

from ..models.entities import Event, User
from ..repositories import user_repository
from .errors import ForbiddenError, NotFoundError, RuleError


def get_actor(connection: sqlite3.Connection, actor_id: int) -> User:
    """Carrega quem está fazendo a requisição."""
    actor = user_repository.get_user_by_id(connection, actor_id)
    if actor is None:
        raise NotFoundError("Usuário autenticado não encontrado.")
    return actor


def is_admin_or_responsible(actor: User, event: Event) -> bool:
    """Administrador pode tudo; professor só no evento que ele coordena (RN03)."""
    return actor.is_admin or (actor.is_teacher and actor.id == event.responsible_id)


def require_event_manager(
    connection: sqlite3.Connection, actor_id: int, event: Event
) -> User:
    """Exige Administrador ou Professor responsável pelo evento."""
    actor = get_actor(connection, actor_id)
    if not is_admin_or_responsible(actor, event):
        raise ForbiddenError(
            "A operação exige perfil Administrador ou Professor responsável pelo evento."
        )
    return actor


def require_staff(connection: sqlite3.Connection, actor_id: int) -> User:
    """Exige perfil de equipe (Administrador ou Professor)."""
    actor = get_actor(connection, actor_id)
    if not actor.is_staff:
        raise ForbiddenError("Somente Administrador ou Professor pode fazer esta operação.")
    return actor


def require_managers_user(connection: sqlite3.Connection, user_id: int) -> User:
    """Garante que o responsável/coordenador informado existe e é da equipe."""
    responsible = get_actor(connection, user_id)
    if not responsible.is_staff:
        raise RuleError("O responsável pelo evento deve ser Administrador ou Professor.")
    return responsible


def can_act_for_user(actor: User, target_user_id: int) -> bool:
    """Administrador/professor agem por qualquer um; participante só por si (RN04)."""
    return actor.id == target_user_id or actor.is_staff