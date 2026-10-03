"""Rotas de inscrições, presença e certificados."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from ....core.config import settings
from ....core.deps import get_current_user_id
from ....models.entities import RegistrationStatus
from ....schemas.registration import (
    AttendanceUpdate,
    CertificateRead,
    RegistrationCreate,
    RegistrationRead,
)
from ....services import registration_service

router = APIRouter(prefix="/inscricoes", tags=["Inscrições"])


@router.post(
    "",
    response_model=RegistrationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Faz uma inscrição",
)
def realizar_inscricao(
    payload: RegistrationCreate,
    actor_id: int = Depends(get_current_user_id),
) -> RegistrationRead:
    return registration_service.create_registration(
        actor_id=actor_id, user_id=payload.user_id, event_id=payload.event_id
    )


@router.get("", response_model=list[RegistrationRead], summary="Consulta inscrições")
def consultar_inscricoes(
    user_id: Optional[int] = Query(default=None, gt=0),
    event_id: Optional[int] = Query(default=None, gt=0),
    situacao: Optional[RegistrationStatus] = Query(
        default=None, alias="status", description="inscrita ou cancelada"
    ),
    limit: int = Query(default=settings.default_page_size, ge=1, le=settings.max_page_size),
    offset: int = Query(default=0, ge=0),
    actor_id: int = Depends(get_current_user_id),
) -> list[RegistrationRead]:
    """Participante recebe apenas as próprias inscrições (RS04)."""
    return registration_service.list_registrations(
        actor_id=actor_id,
        user_id=user_id,
        event_id=event_id,
        status=situacao.value if situacao else None,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/{registration_id}/cancelar",
    response_model=RegistrationRead,
    summary="Cancela a inscrição (24h de antecedência)",
)
def cancelar_inscricao(
    registration_id: int, actor_id: int = Depends(get_current_user_id)
) -> RegistrationRead:
    return registration_service.cancel_registration(
        actor_id=actor_id, registration_id=registration_id
    )


@router.delete(
    "/{registration_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Exclui uma inscrição (Administrador ou responsável)",
)
def excluir_inscricao(
    registration_id: int, actor_id: int = Depends(get_current_user_id)
) -> None:
    registration_service.delete_registration(
        actor_id=actor_id, registration_id=registration_id
    )


@router.patch(
    "/{registration_id}/presenca",
    response_model=RegistrationRead,
    summary="Confirma ou desfaz a presença",
)
def confirmar_presenca(
    registration_id: int,
    payload: AttendanceUpdate,
    actor_id: int = Depends(get_current_user_id),
) -> RegistrationRead:
    return registration_service.update_attendance(
        actor_id=actor_id, registration_id=registration_id, attended=payload.attended
    )


@router.get(
    "/{registration_id}/certificado",
    response_model=CertificateRead,
    summary="Emite o certificado",
)
def emitir_certificado(
    registration_id: int, actor_id: int = Depends(get_current_user_id)
) -> CertificateRead:
    return registration_service.issue_certificate(
        actor_id=actor_id, registration_id=registration_id
    )