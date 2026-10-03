"""Segurança do sistema: senhas e token de acesso.

As senhas NUNCA são salvas como o usuário digitou. Elas passam pelo PBKDF2
(disponível na biblioteca padrão do Python, sem dependência extra) e o banco
guarda apenas o resultado do hash junto com o "sal" aleatório.

O token de acesso é uma versão simples de JWT: um JSON em base64 assinado com
HMAC-SHA256. Serve muito bem para o estudo e não precisa de biblioteca extra.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Optional

from .config import settings

ALGORITHM = "pbkdf2_sha256"
SALT_SIZE = 16


class TokenError(Exception):
    """Erro levantado quando o token é inválido, expirado ou adulterado."""


def hash_password(password: str) -> str:
    """Gera o hash da senha no formato algoritmo$iterações$sal$hash."""
    salt = os.urandom(SALT_SIZE)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, settings.password_iterations
    )
    return (
        f"{ALGORITHM}${settings.password_iterations}"
        f"${salt.hex()}${digest.hex()}"
    )


def verify_password(password: str, stored_hash: str) -> bool:
    """Confere a senha digitada contra o hash salvo no banco."""
    if not stored_hash or stored_hash.count("$") != 3:
        return False

    algorithm, iterations, salt_hex, digest_hex = stored_hash.split("$")
    if algorithm != ALGORITHM:
        return False

    try:
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations)
        )
    except (ValueError, TypeError):
        return False

    # compare_digest evita comparação "palpite por palpite" (timing attack).
    return hmac.compare_digest(digest.hex(), digest_hex)


def _encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _decode(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def _sign(payload: str) -> str:
    signature = hmac.new(
        settings.secret_key.encode("utf-8"), payload.encode("ascii"), hashlib.sha256
    ).digest()
    return _encode(signature)


def create_access_token(user_id: int, expires_minutes: Optional[int] = None) -> str:
    """Monta o token com o id do usuário e a data de expiração."""
    minutes = expires_minutes or settings.token_expire_minutes
    payload = _encode(
        json.dumps(
            {"sub": int(user_id), "exp": int(time.time()) + minutes * 60},
            separators=(",", ":"),
        ).encode("utf-8")
    )
    return f"{payload}.{_sign(payload)}"


def decode_access_token(token: str) -> int:
    """Confere a assinatura e devolve o id do usuário do token."""
    if not token or token.count(".") != 1:
        raise TokenError("Token malformado.")

    payload, signature = token.split(".")
    if not hmac.compare_digest(_sign(payload), signature):
        raise TokenError("Assinatura do token não confere.")

    try:
        data = json.loads(_decode(payload))
        user_id = int(data["sub"])
        expires_at = int(data["exp"])
    except (ValueError, TypeError, KeyError):
        raise TokenError("Conteúdo do token inválido.") from None

    if expires_at < int(time.time()):
        raise TokenError("Token expirado. Faça login novamente.")
    if user_id <= 0:
        raise TokenError("Token sem usuário válido.")
    return user_id