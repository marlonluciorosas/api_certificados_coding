"""Dependências compartilhadas pelas rotas.

Aqui descobrimos QUEM está fazendo a requisição. Aceitamos duas formas:

1. `Authorization: Bearer <token>` -> forma correta, gerada pelo /auth/login;
2. `X-User-Id: <id>`               -> mantida para não quebrar os testes
   antigos da atividade e para facilitar o uso no Swagger.

Em um sistema de produção a segunda opção sairia do código, porque qualquer
pessoa poderia "dizer" que é outro usuário.
"""
from __future__ import annotations

from typing import Optional

from fastapi import Depends, Header, HTTPException, status

from ..models.entities import User
from ..services import user_service
from .security import TokenError, decode_access_token


def get_current_user_id(
    authorization: Optional[str] = Header(default=None),
    x_user_id: Optional[int] = Header(default=None, alias="X-User-Id"),
) -> int:
    """Devolve o id do usuário da requisição ou responde 401."""
    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Cabeçalho Authorization inválido. Use: Bearer <token>.",
            )
        try:
            return decode_access_token(token.strip())
        except TokenError as error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail=str(error)
            ) from error

    if x_user_id is not None and x_user_id > 0:
        return x_user_id

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=(
            "Não identifiquei o usuário. Faça login em POST /api/v1/auth/login "
            "e envie o token em Authorization: Bearer <token>."
        ),
    )


def get_current_user(user_id: int = Depends(get_current_user_id)) -> User:
    """Carrega o usuário completo (o serviço responde 404 se não existir)."""
    return user_service.get_user(user_id)
