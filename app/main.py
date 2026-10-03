"""Aplicação FastAPI do Atividade de Victor lalala.

Aluno: Victor Ricardo Batista de Araújo
Curso: Análise e Desenvolvimento de Sistemas (ADS)

Este arquivo monta a aplicação: cria as tabelas quando o servidor sobe,
registra o tratador de erros de negócio e liga os routers.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .api.v1.api import api_router
from .api.v1.routers import info
from .core.config import settings
from .database.session import init_db
from .services.errors import ServiceError

DESCRIPTION = """
API para cadastro de **usuários**, **cursos** e **eventos**, com inscrições,
controle de presença e emissão de certificados.

### Como usar
1. Cadastre-se em `POST /api/v1/usuarios` (informe e-mail e senha);
2. Faça login em `POST /api/v1/auth/login` e copie o `access_token`;
3. Clique em **Authorize** e informe o token para acessar as rotas protegidas.

Também é possível identificar-se pelo cabeçalho `X-User-Id`, que é a forma
usada nos primeiros testes da atividade.
"""


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Executa na subida e na descida do servidor.

    Troquei o antigo `@app.on_event("startup")` (que está descontinuado no
    FastAPI) pelo `lifespan`, que é a forma recomendada atualmente.
    """
    init_db()
    if settings.seed_on_startup:
        # Import feito aqui dentro para não pesar a subida da API.
        from .database.seed import populate_database

        populate_database()
    yield


app = FastAPI(
    title=settings.project_name,
    description=DESCRIPTION,
    version=settings.version,
    contact={"name": settings.author, "curso": settings.course},
    lifespan=lifespan,
)


@app.exception_handler(ServiceError)
async def service_error_handler(request: Request, exc: ServiceError) -> JSONResponse:
    """Transforma qualquer erro de regra de negócio em uma resposta JSON."""
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


# Rotas de apresentação continuam na raiz (compatibilidade com a atividade).
app.include_router(info.router)

# Rotas do sistema, agora versionadas em /api/v1.
app.include_router(api_router, prefix=settings.api_prefix)