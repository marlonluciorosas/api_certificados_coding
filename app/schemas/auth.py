"""Schemas de autenticação."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .user import UserRead


class LoginRequest(BaseModel):
    """Dados do login."""

    model_config = ConfigDict(str_strip_whitespace=True)

    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    """Resposta do login: o token e os dados de quem entrou."""

    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: UserRead
