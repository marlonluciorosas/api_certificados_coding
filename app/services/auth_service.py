"""Regras de negócio da autenticação (login com e-mail e senha)."""
from __future__ import annotations

from ..core.security import create_access_token, verify_password
from ..database.session import get_connection
from ..models.entities import User
from ..repositories import user_repository
from .errors import UnauthorizedError


def authenticate(email: str, password: str) -> User:
    """Confere e-mail e senha e devolve o usuário.

    A mensagem de erro é sempre a mesma (não diz se o e-mail existe), para não
    dar pistas a quem estiver tentando adivinhar senhas (RS01).
    """
    connection = get_connection()
    try:
        user = user_repository.get_user_by_email(connection, email)
    finally:
        connection.close()

    if user is None or not verify_password(password, user.password_hash):
        raise UnauthorizedError("E-mail ou senha incorretos.")
    return user


def login(email: str, password: str) -> tuple[User, str]:
    """Autentica e já devolve o token de acesso."""
    user = authenticate(email, password)
    return user, create_access_token(user.id)