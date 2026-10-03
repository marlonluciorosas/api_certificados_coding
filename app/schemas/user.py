"""Schemas de usuário: validam a entrada e organizam a saída da API."""
from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..models.entities import UserRole

EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class UserCreate(BaseModel):
    """Dados para cadastrar um usuário (RN08 e RS03)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=6, max_length=128)
    role: UserRole = UserRole.PARTICIPANTE
    course_id: Optional[int] = Field(default=None, gt=0)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not EMAIL_PATTERN.fullmatch(value):
            raise ValueError("Informe um endereço de e-mail válido.")
        return value

    @field_validator("password")
    @classmethod
    def password_must_be_strong_enough(cls, value: str) -> str:
        """A senha precisa ter letra e número (RN09 é da carga horária)."""
        if not any(char.isalpha() for char in value):
            raise ValueError("A senha deve conter pelo menos uma letra.")
        if not any(char.isdigit() for char in value):
            raise ValueError("A senha deve conter pelo menos um número.")
        return value


class UserRead(BaseModel):
    """Usuário devolvido pela API. Repare que a senha nunca aparece aqui."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role: UserRole
    course_id: Optional[int] = None
    course_name: Optional[str] = None
    created_at: datetime