"""Erros de regra de negócio.

Cada erro já carrega o código HTTP que a API deve responder. Assim as rotas não
precisam tratar exceção nenhuma: o `app/main.py` tem um tratador único para
ServiceError.

Observação: a versão anterior chamava o erro de permissão de `PermissionError`,
que é o nome de um erro embutido do Python. Renomeei para `ForbiddenError` para
não confundir quem lê o código (e evitar capturar o erro errado).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ServiceError(Exception):
    """Erro de negócio com status HTTP e mensagem para o cliente."""

    status_code: int
    detail: str

    def __str__(self) -> str:  # ajuda no log do servidor
        return f"{self.status_code}: {self.detail}"


class NotFoundError(ServiceError):
    """404 - o registro não existe."""

    def __init__(self, detail: str = "Registro não encontrado.") -> None:
        super().__init__(404, detail)


class ConflictError(ServiceError):
    """409 - o pedido conflita com o estado atual (duplicidade, lotação, etc.)."""

    def __init__(self, detail: str) -> None:
        super().__init__(409, detail)


class RuleError(ServiceError):
    """400 - o pedido desrespeita uma regra de negócio."""

    def __init__(self, detail: str) -> None:
        super().__init__(400, detail)


class UnauthorizedError(ServiceError):
    """401 - não foi possível identificar/autenticar o usuário."""

    def __init__(self, detail: str = "Não autorizado.") -> None:
        super().__init__(401, detail)


class ForbiddenError(ServiceError):
    """403 - o usuário foi identificado, mas não tem permissão."""

    def __init__(self, detail: str = "Usuário sem permissão para esta operação.") -> None:
        super().__init__(403, detail)