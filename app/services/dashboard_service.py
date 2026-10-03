"""Monta um resumo simples para a página inicial do usuário.

A ideia é fazer algo útil sem criar uma camada enorme de relatórios. O aluno
consegue ver quantas inscrições tem, em quais eventos esteve presente e quais
certificados já pode emitir.
"""
from __future__ import annotations

from ..database.converters import now_utc
from ..database.session import get_connection
from ..models.entities import Event
from ..repositories import event_repository, registration_repository, user_repository
from .errors import NotFoundError


# O banco tem no máximo 200 registros nesta consulta, suficiente para o painel
# da atividade e evita trazer uma tabela inteira por acidente.
DASHBOARD_LIMIT = 200


def get_dashboard(user_id: int) -> dict:
    """Devolve os números pessoais e os próximos eventos do usuário."""
    connection = get_connection()
    try:
        user = user_repository.get_user_by_id(connection, user_id)
        if user is None:
            raise NotFoundError("Usuário não encontrado.")

        registrations = registration_repository.list_registrations(
            connection,
            user_id=user_id,
            limit=DASHBOARD_LIMIT,
            offset=0,
        )
        active = [registration for registration in registrations if registration.is_active]
        present = [registration for registration in registrations if registration.attended]
        certificates = [registration for registration in active if registration.attended]

        # Pega os eventos correspondentes às inscrições ativas e ordena pela data.
        # Uma inscrição cancelada não aparece nos próximos eventos.
        upcoming_events: list[Event] = []
        for registration in active:
            event = event_repository.get_event_by_id(connection, registration.event_id)
            if event is not None and not event.finished:
                upcoming_events.append(event)

        upcoming_events.sort(key=lambda event: (event.start_at, event.id))
        # A tela inicial não precisa mostrar uma lista enorme.
        upcoming_events = upcoming_events[:5]

        return {
            "user_id": user.id,
            "user_name": user.name,
            "role": user.role,
            "total_inscricoes": len(registrations),
            "inscricoes_ativas": len(active),
            "presencas_confirmadas": len(present),
            "certificados_disponiveis": len(certificates),
            "proxima_inscricao": (
                upcoming_events[0].start_at if upcoming_events else None
            ),
            "proximos_eventos": upcoming_events,
        }
    finally:
        connection.close()
