"""Rotas de eventos."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from ....core.config import settings
from ....core.deps import get_current_user_id
from ....schemas.event import EventCreate, EventRead, EventUpdate
from ....services import event_service

router = APIRouter(prefix="/eventos", tags=["Eventos"])


@router.post(
    "",
    response_model=EventRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra um evento (Administrador ou Professor)",
)
def cadastrar_evento(
    payload: EventCreate, actor_id: int = Depends(get_current_user_id)
) -> EventRead:
    return event_service.create_event(
        actor_id=actor_id,
        title=payload.title,
        description=payload.description,
        start_at=payload.start_at,
        location=payload.location,
        capacity=payload.capacity,
        duration_hours=payload.duration_hours,
        responsible_id=payload.responsible_id,
        course_id=payload.course_id,
    )


@router.get("", response_model=list[EventRead], summary="Lista os eventos")
def consultar_eventos(
    limit: int = Query(default=settings.default_page_size, ge=1, le=settings.max_page_size),
    offset: int = Query(default=0, ge=0),
    course_id: Optional[int] = Query(default=None, gt=0, description="Filtra por curso"),
    busca: Optional[str] = Query(
        default=None,
        min_length=2,
        max_length=80,
        description="Procura no título, descrição ou local",
    ),
    futuros: bool = Query(default=False, description="Mostra apenas eventos futuros"),
) -> list[EventRead]:
    return event_service.list_events(
        limit=limit,
        offset=offset,
        course_id=course_id,
        search=busca,
        future_only=futuros,
    )


@router.get("/{event_id}", response_model=EventRead, summary="Consulta um evento")
def consultar_evento(event_id: int) -> EventRead:
    return event_service.get_event(event_id)


@router.patch(
    "/{event_id}",
    response_model=EventRead,
    summary="Edita um evento (Administrador ou responsável)",
)
def editar_evento(
    event_id: int,
    payload: EventUpdate,
    actor_id: int = Depends(get_current_user_id),
) -> EventRead:
    # exclude_unset=True: só os campos que vieram no JSON entram na edição.
    return event_service.update_event(
        actor_id=actor_id,
        event_id=event_id,
        changes=payload.model_dump(exclude_unset=True),
    )


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Exclui um evento (Administrador ou responsável)",
)
def excluir_evento(event_id: int, actor_id: int = Depends(get_current_user_id)) -> None:
    event_service.delete_event(actor_id=actor_id, event_id=event_id)
