"""Rotas de autenticação."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from ....core.config import settings
from ....core.deps import get_current_user
from ....models.entities import User
from ....schemas.auth import LoginRequest, TokenResponse
from ....schemas.user import UserRead
from ....services import auth_service

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Faz login e devolve o token de acesso",
)
def login(payload: LoginRequest) -> TokenResponse:
    """Compara a senha digitada com o hash salvo e gera o token."""
    user, token = auth_service.login(payload.email, payload.password)
    return TokenResponse(
        access_token=token,
        expires_in_minutes=settings.token_expire_minutes,
        user=UserRead.model_validate(user),
    )


@router.get("/me", response_model=UserRead, summary="Mostra o usuário do token")
def eu(user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(user)