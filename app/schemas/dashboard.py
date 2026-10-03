"""Schema da tela-resumo do usuário.

É uma resposta pequena para a futura tela inicial do sistema. Em vez de o
frontend fazer várias consultas, ele chama uma rota e recebe os números mais
importantes junto com os próximos eventos.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from .event import EventRead


class DashboardRead(BaseModel):
    """Resumo pessoal do usuário logado."""

    model_config = ConfigDict(from_attributes=True)

    user_id: int
    user_name: str
    role: str
    total_inscricoes: int
    inscricoes_ativas: int
    presencas_confirmadas: int
    certificados_disponiveis: int
    proxima_inscricao: Optional[datetime] = None
    proximos_eventos: list[EventRead] = Field(default_factory=list)
