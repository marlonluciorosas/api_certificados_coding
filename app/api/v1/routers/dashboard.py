"""Rota do painel inicial do usuário."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from ....core.deps import get_current_user_id
from ....schemas.dashboard import DashboardRead
from ....services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("", response_model=DashboardRead, summary="Mostra um resumo do usuário logado")
def consultar_dashboard(actor_id: int = Depends(get_current_user_id)) -> DashboardRead:
    """Retorna inscrições, presenças, certificados e próximos eventos."""
    return dashboard_service.get_dashboard(actor_id)