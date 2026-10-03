"""Rotas de usuários."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from ....core.config import settings
from ....core.deps import get_current_user_id
from ....schemas.user import UserCreate, UserRead
from ....services import user_service

router = APIRouter(prefix="/usuarios", tags=["Usuários"])


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra um usuário",
)
def cadastrar_usuario(payload: UserCreate) -> UserRead:
    """Rota aberta: é por aqui que o aluno cria a própria conta."""
    return user_service.create_user(
        name=payload.name,
        email=payload.email,
        password=payload.password,
        role=payload.role.value,
        course_id=payload.course_id,
    )


@router.get("", response_model=list[UserRead], summary="Lista usuários (paginado)")
def consultar_usuarios(
    limit: int = Query(default=settings.default_page_size, ge=1, le=settings.max_page_size),
    offset: int = Query(default=0, ge=0),
    actor_id: int = Depends(get_current_user_id),
) -> list[UserRead]:
    """A lista de usuários só é liberada para quem está autenticado (RS04)."""
    return user_service.list_users(limit=limit, offset=offset)


@router.get("/{user_id}", response_model=UserRead, summary="Consulta um usuário")
def consultar_usuario(
    user_id: int, actor_id: int = Depends(get_current_user_id)
) -> UserRead:
    return user_service.get_user(user_id)