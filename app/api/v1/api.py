"""Junta todas as rotas da versão 1 da API.

Este arquivo é o único lugar onde as rotas são registradas. Quando surgir uma
versão 2, basta criar `app/api/v2` e incluir aqui (ou no main.py), sem mexer na
v1 que já está em uso.
"""
from __future__ import annotations

from fastapi import APIRouter

from .routers import auth, cursos, dashboard, eventos, inscricoes, usuarios

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(usuarios.router)
api_router.include_router(cursos.router)
api_router.include_router(eventos.router)
api_router.include_router(inscricoes.router)
